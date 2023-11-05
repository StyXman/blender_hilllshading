# blender_hilllshading

Generate hillshading from DEM files using Blender.

It's a scripted and slightly enhanced version of Daniel Huffman's famous
[Blender Relief Tutorial](https://somethingaboutmaps.wordpress.com/blender-relief-tutorial-getting-set-up/)

Try to use the `main` branch; `develop` is considered unstable and can be broken.

## Dependencies

Requires:

* Blender (not installable via pip)
* rasterio, built with v1.3.9.

## Caveats

* This method as it is right now has issues at the seams, so for the moment it can only be applied to a single DEM file
  which should be bigger than your desired are of coverage.

* The script is not 100% parametrized. Sun size and power are fixed based on my tests

* I will try to add a scattering sky, so we get a bluish tint to the shadows, and set the Sun's color to something
  yellowish.

* This hillshading method is really sensible to missing or bad data, because they look like dark, deep holes.


## Samples

A couple of images of the shadows applied to my style as teaser, both using only 20 samples and x10 height scale:

Dhaulagiri:

![NO-ALT](https://www.grulic.org.ar/~mdione/glob/images/Dhaulagiri.jpg)

Mont Blanc/Monte Bianco:

![NO-ALT](https://www.grulic.org.ar/~mdione/glob/images/Mont_Blanc-Monte_Bianco.jpg)

Man, I love the fact that the tail of the Giacchiaio del Miage is in shadows, but the rest is not; or how
Monte Bianco/Mont Blanc's shadow reaches across the Val Vény to the base of la Tête d'Arp. But also notice the bad data
close to la Mer de Glace.
