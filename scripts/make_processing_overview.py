from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer
root = Path(__file__).resolve().parent.parent
source = root / "source_snapshot"
cfg = json.loads((source/'config/study_area.json').read_text())
project = Transformer.from_crs(4326,2326,always_xy=True)
extents = {}
for label in ('core','acquisition'):
    w,s,e,n = cfg[label+'_bbox']
    points = [project.transform(x,y) for x,y in [(w,s),(w,n),(e,s),(e,n)]]
    xmin,ymin = min(p[0] for p in points),min(p[1] for p in points)
    xmax,ymax = max(p[0] for p in points),max(p[1] for p in points)
    extents[label] = dict(projected_envelope=[xmin,ymin,xmax,ymax],
                          approximate_width_m=xmax-xmin,approximate_height_m=ymax-ymin)
missing = []
for kind in ('dsm','dtm'):
    index = json.loads((source/f'data/raw/cedd/indexes/{kind}_mongkok.geojson').read_text())
    for feature in index['features']:
        filename = feature['properties']['FILENAME']
        if not (source/'data/raw/cedd'/kind/filename).is_file():
            missing.append(f'{kind}/{filename}')

# Illustration from real tile-index geometry. No fabricated elevation or SVF.
canvas = Image.new('RGB',(1700,1120),'#f3f6fa')
draw = ImageDraw.Draw(canvas)
fontpath = '/System/Library/Fonts/Supplemental/Arial.ttf'
font = lambda size: ImageFont.truetype(fontpath,size)
draw.text((60,40),'MONG KOK | data preparation overview',font=font(40),fill='#142b43')
draw.text((60,95),'Coverage plan from the saved CEDD index - no SVF or mosaic result is shown',font=font(24),fill='#52657b')
draw.rounded_rectangle((45,155,1050,1015),20,fill='white')
draw.rounded_rectangle((1080,155,1655,1015),20,fill='white')
features=json.loads((source/'data/raw/cedd/indexes/dsm_mongkok.geojson').read_text())['features']
geometries=[]
for feature in features:
    ring=feature['geometry']['coordinates'][0]
    geometries.append((feature['properties']['TILE_NAME'],[project.transform(*p) for p in ring]))
allpoints=[p for _,ring in geometries for p in ring]
xmin,xmax=min(p[0] for p in allpoints),max(p[0] for p in allpoints)
ymin,ymax=min(p[1] for p in allpoints),max(p[1] for p in allpoints)
scale=min(850/(xmax-xmin),580/(ymax-ymin))
cx,cy=545,565
def pixel(x,y):
    return (cx+(x-(xmin+xmax)/2)*scale,cy-(y-(ymin+ymax)/2)*scale)
for label,ring in geometries:
    shape=[pixel(*p) for p in ring]
    draw.polygon(shape,fill='#e4edf7',outline='#8099b1',width=3)
    center=pixel(sum(x for x,y in ring[:-1])/len(ring[:-1]),sum(y for x,y in ring[:-1])/len(ring[:-1]))
    draw.text(center,label,font=font(19),fill='#637b92',anchor='mm')
for label,color,width in [('acquisition','#e88b26',6),('core','#087f88',7)]:
    w,s,e,n=extents[label]['projected_envelope']
    corners=[pixel(w,s),pixel(e,s),pixel(e,n),pixel(w,n),pixel(w,s)]
    draw.line(corners,fill=color,width=width)
draw.text((85,190),'9 indexed tiles for each layer',font=font(27),fill='#142b43')
draw.text((85,230),'EPSG:2326 / Hong Kong 1980 Grid',font=font(20),fill='#52657b')
draw.line((90,900,145,900),fill='#e88b26',width=7)
draw.text((165,883),'Acquisition: approximately 1 km x 1 km',font=font(22),fill='#142b43')
draw.line((90,950,145,950),fill='#087f88',width=7)
draw.text((165,933),'Core: approximately 500 m x 500 m',font=font(22),fill='#142b43')
draw.text((1110,190),'Workflow and current status',font=font(27),fill='#142b43')
steps=[('1  Preserve originals','Original PhD folder unchanged.','#dcefe9'),
       ('2  Separate working copy','Copies, scripts and records in Downloads.','#dcefe9'),
       ('3  Verify local raster inputs','BLOCKED: 18 ZIPs absent from source.','#fff0d6'),
       ('4  Mosaic DSM and DTM separately','Prepared script; execution pending inputs.','#e9edf3'),
       ('5  Clip acquisition and core','Four clips planned; no outputs claimed.','#e9edf3'),
       ('6  Compute SVF later','Use acquisition; map results in core.','#e9edf3')]
for i,(title,body,color) in enumerate(steps):
    y=255+i*110
    draw.rounded_rectangle((1105,y,1630,y+90),12,fill=color)
    draw.text((1120,y+13),title,font=font(23),fill='#142b43')
    draw.text((1120,y+52),body,font=font(19),fill='#52657b')
draw.text((65,1050),'Missing local input files prevent full mosaic/clip validation. Tile footprints do not prove raster availability.',font=font(23),fill='#70521c')
canvas.save(root/'figures/processing_overview.png')

