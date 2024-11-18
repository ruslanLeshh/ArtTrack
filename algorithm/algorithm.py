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

# configuration
USER_IMAGES_DIR = 'algorithm/user_images'
NEW_IMAGES_DIR = 'algorithm/new_images'
BATCH_SIZE = 16
NUM_NEIGHBORS = 5
IMAGE_SIZE = (224, 224)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


class FeatureExtractor:
    def __init__(self, device: torch.device = DEVICE):
        """initialize the feature extractor with a pre-trained model"""
        self.device = device
        self.model = models.resnet50(pretrained=True)
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
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    image_paths = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(supported_formats):
            image_paths.append(os.path.join(directory, filename))
    return image_paths


def main():
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

    # build faiss index
    dimension = user_vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(user_vectors)
    logging.info(f"faiss index created with dimension {dimension}")

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

    # search for nearest neighbors
    distances, indices = index.search(new_vectors, NUM_NEIGHBORS)
    for i, new_filename in enumerate(new_filenames):
        logging.info(f"nearest images to {new_filename}:")
        for idx in indices[i]:
            user_filename = user_filenames[idx]
            logging.info(f" - {user_filename}")  # output nearest neighbor filename


if __name__ == "__main__":
    main()
