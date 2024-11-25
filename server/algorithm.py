import os
import sys
import logging
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import faiss
from typing import List
import json

# configuration
USER_IMAGES_DIR = 'images/users-images'
NEW_IMAGES_DIR = 'images/internet-images'
BATCH_SIZE = 16
NUM_NEIGHBORS = 5
IMAGE_SIZE = (224, 224)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')  # remove timestamp


class FeatureExtractor:
    def __init__(self, device: torch.device = DEVICE):
        """initialize the feature extractor with a pre-trained model"""
        self.device = device
        self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.model.fc = nn.Identity()  # remove the last layer
        self.model.to(self.device)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
        ])

    def extract_features(self, image_paths: List[str]) -> np.ndarray:
        """
        extract feature vectors from a list of image paths

        :param image_paths: list of image file paths
        :return: numpy array of feature vectors
        """
        images = []
        for image_path in image_paths:
            try:
                image = Image.open(image_path).convert('RGB')
                image = self.transform(image)
                images.append(image)
            except Exception as e:
                logging.error(f"error processing image {image_path}: {e}")  # log error if image processing fails
        if not images:
            return np.array([])
        images = torch.stack(images).to(self.device)
        with torch.no_grad():
            features = self.model(images)
        return features.cpu().numpy()


def load_image_paths(directory: str) -> List[str]:
    """
    load image file paths from a directory, filtering by supported formats

    :param directory: directory to search for images
    :return: list of image file paths
    """
    
    image_paths = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            with Image.open(file_path) as img:
                image_paths.append(file_path)
        except (IOError, ValueError): continue
    return image_paths


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """normalize vectors to unit length"""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms


def scan():
    # load image paths
    user_image_paths = load_image_paths(USER_IMAGES_DIR)
    new_image_paths = load_image_paths(NEW_IMAGES_DIR)
    logging.info(f"found {len(user_image_paths)} user images")
    logging.info(f"found {len(new_image_paths)} new images")

    # initialize feature extractor
    extractor = FeatureExtractor()

    # extract features for user images
    user_vectors = []
    user_filenames = []
    for i in range(0, len(user_image_paths), BATCH_SIZE):
        batch_paths = user_image_paths[i:i+BATCH_SIZE]
        features = extractor.extract_features(batch_paths)
        if features.size > 0:
            user_vectors.append(features)
            user_filenames.extend([os.path.basename(p) for p in batch_paths])  # keep track of filenames
    if not user_vectors:
        logging.error("no user images were processed successfully")
        sys.exit(1)
    user_vectors = np.vstack(user_vectors).astype('float32')
    user_vectors = normalize_vectors(user_vectors)  # normalize user vectors
    # print("\nUSER VECTORS", user_vectors)
    # print("\nUSER FILENAMES", user_filenames)
    
    # build faiss index
    dimension = user_vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)  # use inner product for cosine similarity
    index.add(user_vectors)
    logging.info(f"faiss index created with dimension {dimension}")
    faiss.write_index(index, "user_vector_index.faiss")

    # extract features for new images
    new_vectors = []
    new_filenames = []
    for i in range(0, len(new_image_paths), BATCH_SIZE):
        batch_paths = new_image_paths[i:i+BATCH_SIZE]
        features = extractor.extract_features(batch_paths)
        if features.size > 0:
            new_vectors.append(features)
            new_filenames.extend([os.path.basename(p) for p in batch_paths])  # keep track of filenames
    if not new_vectors:
        logging.error("no new images were processed successfully")
        sys.exit(1)
    new_vectors = np.vstack(new_vectors).astype('float32')
    new_vectors = normalize_vectors(new_vectors)  # normalize new vectors
    # print("\nNEW VECTORS", new_vectors)
    # print("\nNEW FILENAMES", new_filenames)

    # search for nearest neighbors
    matches = []
    distances, indices = index.search(new_vectors, NUM_NEIGHBORS)
    for i, new_filename in enumerate(new_filenames):
        # logging.info(f"nearest images to {new_filename}:")
        for similarity, idx in zip(distances[i], indices[i]):
            user_filename = user_filenames[idx]
            percentage_similarity = ((similarity + 1) / 2) * 100  # map from [-1,1] to [0,100]
            # logging.info(f" - {user_filename}, similarity: {percentage_similarity:.2f}%")  # output with percentage
            if percentage_similarity >= 90:
                matched_image = {
                    "new_filename": new_filename,
                    "user_filename": user_filenames[idx],
                    "similarity": percentage_similarity
                }
                matches.append(matched_image)
    return matches

# we find matches for ne images from users images