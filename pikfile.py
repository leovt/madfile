import os.path
from PIL import Image
import madfile

def pik2img(in_name, out_name=None, palette_name=None):
    if out_name is None:
        out_name = os.path.splitext(in_name)[0] + '.png'

    sect = madfile.read(in_name)
    pik_header = sect[0]
    height = pik_header[0]+256*pik_header[1]
    width = pik_header[2]+256*pik_header[3]

    pixels = sect[1]
    assert len(pixels) == width * height

    assert len(sect) in (2, 3)

    if len(sect) < 3:
        if palette_name:
            with open(palette_name, 'rb') as f:
                palette = f.read(768)
        else:
            palette = None
    else:
        palette = sect[2]

    if palette:
        assert len(palette) == 3*256
        assert all(0 <= x < 64 for x in palette)
        mode = 'P'
    else:
        mode = 'L'

    from PIL import Image
    img = Image.new(mode, (width, height))
    img.putdata(pixels)
    if palette:
        img.putpalette([x*4+x//16 for x in palette])
    img.save(os.path.join('pics', out_name))

def img2pik(in_name, out_name=None, use_palette=True):
    if out_name is None:
        out_name = os.path.splitext(in_name)[0] + '.pik'
    img = Image.open(in_name)

    if img.mode != 'P':
        img = img.convert('P')

    pik_header = bytes([img.height % 256, img.height // 256,
                        img.width % 256, img.width // 256,
                        0, 0, 0, 0])

    if use_palette:
        palette = bytes([x // 4 for x in img.getpalette()])
        madfile.write(out_name, [pik_header, bytes(img.getdata()), palette])
    else:
        madfile.write(out_name, [pik_header, bytes(img.getdata())])

if __name__ == '__main__':
    pik2img('/home/leonhard/Games/dosbox/coloniz2/opening.pik')
    img2pik('/home/leonhard/Games/dosbox/coloniz2/banner.jpeg', '/home/leonhard/Games/dosbox/coloniz2/opening.pik')
