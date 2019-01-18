from __future__ import print_function
from torch.autograd import Variable
import os
import time
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
import torchvision
import torchvision.transforms as transforms
import torchvision.utils as vutils
import matplotlib.pyplot as plt

from generator import Generator
from discriminator import Discriminator

model_name = 'space_images'

SAVE_DIR = './models/'
SAVE_FILE = model_name + '_checkpoint.pth.tar'
SAVE_PATH = SAVE_DIR + SAVE_FILE
SAVE_INTERVAL = 10
NUM_EPOCHS = 200

batchSize = 64 # Size of the batch
imageSize = 64 # Size of the generated images

# Directory to save the images
save_dir = "./results/unsorted"

# Lists for plotting
losses_G = []
losses_D = []

# Will apply scaling, tensor conversion, and normalization to the input images
transform = transforms.Compose([transforms.Resize(imageSize), transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),])

# Function to save checkpoint for resuming training from epoch
def save_checkpoint(state, filename = SAVE_DIR + SAVE_FILE):
    torch.save(state, filename)
    print('Saved checkpoint')

# Load directory containing images as a training dataset
def load_dataset():
    data_path = './data'
    train_dataset = torchvision.datasets.ImageFolder(
        root=data_path,
        transform=transform
    )
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batchSize,
        num_workers=0,
        shuffle=True
    )
    return train_loader

dataloader = load_dataset();

# Function to initialize all the weights of a neural network
def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        m.weight.data.normal_(0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        m.weight.data.normal_(1.0, 0.02)
        m.bias.data.fill_(0)

# Function to add gaussian noise to images to stabilize training
def add_gaussian_noise(image, mean, stddev):
    noise = Variable(image.data.new(image.size()).normal_(mean, stddev))
    return image + noise

# Parameters for Gaussian distribution
mean = 0
stddev = 0.05    

# Creating the generator and discriminator
netG = Generator()
netD = Discriminator()

netG.apply(weights_init)
netD.apply(weights_init)

criterion = nn.BCELoss() # Criterion object to measure the loss

# Optimizers for the generator and discriminator
optimizerG = optim.Adam(netG.parameters(), lr = 0.0002, betas = (0.5, 0.999))
optimizerD = optim.Adam(netD.parameters(), lr = 0.0002, betas = (0.5, 0.999))

start_epoch = 0

# Load checkpoint if saved model is found
if os.path.isfile(SAVE_PATH):
    print("Checkpoint found!") 
    time.sleep(2)
        
    checkpoint = torch.load(SAVE_PATH)
    start_epoch = checkpoint['epoch']
    netG.load_state_dict(checkpoint['netG_state_dict'])
    netD.load_state_dict(checkpoint['netD_state_dict'])
    optimizerG.load_state_dict(checkpoint['optimizerG_state_dict'])
    optimizerD.load_state_dict(checkpoint['optimizerD_state_dict'])
    losses_G = checkpoint['losses_G']
    losses_D = checkpoint['losses_D']
else:
    print("No checkpoint found")

# Training the DCGAN
for epoch in range(start_epoch, NUM_EPOCHS):
    # Iterate over each image in the dataset
    for i, data in enumerate(dataloader, 0):
        # Train the discriminator with a real image from the dataset
        netD.zero_grad() #  Initialize to 0 the gradients of the discriminator with respect to the weights
        real, _ = data # Get real image from the dataset
        noisy_real = add_gaussian_noise(real, mean, stddev) # Add Gaussian noise to stabilize training

        input = Variable(noisy_real).cuda()
        output = netD(input) # Output is a value between 0 and 1 for the probability that the input is a real image
        rand = torch.Tensor(input.size()[0]).uniform_(0.7, 1.2) # Label Smoothing - Replace real label with random value between 0.7 and 1.2
        target = Variable(rand).cuda() 
        errD_real = criterion(output, target) # Compute the loss between output and 0.7-1.2 for a real image
        
        # Train the discriminator with a fake image generated by the generator
        noise = Variable(torch.randn(input.size()[0], 100, 1, 1)).cuda() # Pass in random input vector for the generator as noise
        fake = netG(noise) # Get fake generated images
        noisy_fake = add_gaussian_noise(fake, mean, stddev) # Add Gaussian noise to stabilize training
        output = netD(noisy_fake.detach()) # Output is a value between 0 and 1 for the probability that the input is a real image
        rand = torch.Tensor(input.size()[0]).uniform_(0, 0.3) # Label Smoothing - Replace fake label with random value between 0.0 and 0.3
        target = Variable(rand).cuda() 
        errD_fake = criterion(output, target) # Compute the loss between output and 0-0.3 for a fake image

        # Backpropagate the total error for the discriminator and update weights
        errD = errD_real + errD_fake
        errD.backward() # Compute the gradients of the total error with respect to the weights of the discriminator
        optimizerD.step() # Update the weights according to how much they are responsible for the loss of the discriminator

        # Train the generator by aiming for an output of 1 from the discriminator
        netG.zero_grad()
        output = netD(fake) # Output is a value between 0 and 1 for the probability that the input is a real image
        target = Variable(torch.ones(input.size()[0])).cuda() # Compute the loss between output and 1 for the fake generated image
        errG = criterion(output, target)
        errG.backward() # Compute the gradients of the total error with respect to the weights of the generator
        optimizerG.step() # Update the weights according to how much they are responsible for the loss of the generator

        print('[%d/%d][%d/%d] Loss_D: %.4f Loss_G: %.4f' % (epoch, NUM_EPOCHS, i, len(dataloader), errD.item(), errG.item()))
        # Save loss values for plotting
        losses_G.append(errG.item())
        losses_D.append(errD.item())
    
    # Save images every epoch  
    vutils.save_image(real, '%s/real_samples.png' % save_dir, normalize = True) # Save real images of the batch
    fake = netG(noise) # Save fake generated images of the batch
    vutils.save_image(fake.data, '%s/fake_samples_epoch_%03d.png' % (save_dir, epoch), normalize = True) # Save the fake generated images of the minibatch
        
    # Save models for resuming training every set epochs
    if epoch != 0 and epoch % SAVE_INTERVAL == 0:
        save_checkpoint({
            'epoch': epoch + 1,
            'netG_state_dict': netG.state_dict(),
            'netD_state_dict': netD.state_dict(),
            'optimizerG_state_dict': optimizerG.state_dict(),
            'optimizerD_state_dict': optimizerD.state_dict(),
            'losses_G': losses_G,
            'losses_D': losses_D
        })
        
    # Plot generator and discriminator losses per training iterations
    plt.figure(figsize = (10, 5))
    plt.title("Generator and Discriminator Loss During Training")
    plt.plot(losses_G, label = "G")
    plt.plot(losses_D, label = "D")
    plt.xlabel("Iterations")
    plt.ylabel("Loss")
    plt.legend()
    plt.show()