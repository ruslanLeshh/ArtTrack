import os
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
import faiss
from torchvision import models

# ResNet50
model = models.resnet50(pretrained=True)
model.fc = torch.nn.Identity() 
model.eval()


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def extract_feature(image_path):
    image = Image.open(image_path).convert('RGB')
    img_t = transform(image)
    batch_t = torch.unsqueeze(img_t, 0)
    with torch.no_grad():
        features = model(batch_t)
    return features.numpy()


user_images_dir = 'user_images'
user_vectors = []


for img_file in os.listdir(user_images_dir):
    img_path = os.path.join(user_images_dir, img_file)
    vector = extract_feature(img_path)
    user_vectors.append(vector)

user_vectors = np.vstack(user_vectors).astype('float32')


dimension = user_vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(user_vectors)


new_images_dir = 'new_images'
new_vectors = []


for img_file in os.listdir(new_images_dir):
    img_path = os.path.join(new_images_dir, img_file)
    vector = extract_feature(img_path)
    new_vectors.append(vector)

new_vectors = np.vstack(new_vectors).astype('float32')


k = 5 
distances, indices = index.search(new_vectors, k)


for i, img_file in enumerate(os.listdir(new_images_dir)):
    print(f"Найближчі зображення до {img_file}:")
    for idx in indices[i]:
        user_img_file = os.listdir(user_images_dir)[idx]
        print(f" - {user_img_file}")
    print()
