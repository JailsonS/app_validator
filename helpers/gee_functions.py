import ee

def get_sentinel_2_image(geometry: ee.geometry.Geometry, year: int):

    def _remove_cloud(image: ee.image.Image):
        qa_band = image.select('QA60')

        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        
        mask = qa_band.bitwiseAnd(cloud_bit_mask).eq(0).And(
            qa_band.bitwiseAnd(cirrus_bit_mask).eq(0))
        
        return image.updateMask(mask).divide(10000)
    
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(f'{year}-01-01', f'{year}-12-31')
            .filterBounds(geometry)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .map(_remove_cloud)
    )

    image = (   
        ee.Image(collection.median())
        .select(
            ['B8', 'B4', 'B3', 'B2'],
            ['nir', 'red', 'green', 'blue']
        )
    )

    return image
