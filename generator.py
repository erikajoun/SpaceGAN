import torch.nn as nn

# Generator takes in a random input vector as noise and outputs a generated image
class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()
        self.main = nn.Sequential( 
            nn.ConvTranspose2d(100, 512, 4, 1, 0, bias = False), 
            nn.BatchNorm2d(512), 
            nn.ReLU(True), 

            nn.ConvTranspose2d(512, 256, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(256), 
            nn.ReLU(True), 

            nn.ConvTranspose2d(256, 128, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(128), 
            nn.ReLU(True), 

            nn.ConvTranspose2d(128, 64, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(64), 
            nn.ReLU(True),

            nn.ConvTranspose2d(64, 3, 4, 2, 1, bias = False), 
            nn.Tanh()
        ).cuda()

    def forward(self, input): 
        output = self.main(input) 
        return output 
