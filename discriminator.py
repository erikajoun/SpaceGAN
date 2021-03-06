import torch.nn as nn

# Discriminator takes in image as input and outputs probabilty between 0 and 1 that input is a real image
class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.main = nn.Sequential(
            nn.Conv2d(3, 64, 4, 2, 1, bias = False),
            nn.LeakyReLU(0.2, inplace = True),

            nn.Conv2d(64, 128, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(128), 
            nn.LeakyReLU(0.2, inplace = True), 

            nn.Conv2d(128, 256, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(256), 
            nn.LeakyReLU(0.2, inplace = True), 

            nn.Conv2d(256, 512, 4, 2, 1, bias = False), 
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, inplace = True), 

            nn.Conv2d(512, 1, 4, 1, 0, bias = False), 
            nn.Sigmoid() 
        ).cuda()

    def forward(self, input):
        output = self.main(input)
        return output.view(-1)