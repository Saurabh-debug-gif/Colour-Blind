import numpy as np
from PIL import Image

def daltonize(img, mode):
    arr = np.array(img).astype(float)
    R, G, B = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    if mode == "Protanopia":
        R = 0.6*R + 0.4*G
    elif mode == "Deuteranopia":
        G = 0.6*R + 0.4*G

    arr[:,:,0], arr[:,:,1] = R, G
    return Image.fromarray(np.clip(arr,0,255).astype("uint8"))
