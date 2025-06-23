const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function generateFavicons() {
  try {
    const svgPath = path.join(__dirname, '../public/logos/my-taco-icon.svg');
    const svgBuffer = fs.readFileSync(svgPath);
    
    console.log('Generating favicons from SVG...');
    
    // Generate different sizes
    await sharp(svgBuffer)
      .resize(32, 32)
      .png()
      .toFile(path.join(__dirname, '../public/favicon-32x32.png'));
    console.log('✓ Generated favicon-32x32.png');
      
    await sharp(svgBuffer)
      .resize(16, 16)
      .png()
      .toFile(path.join(__dirname, '../public/favicon-16x16.png'));
    console.log('✓ Generated favicon-16x16.png');
      
    await sharp(svgBuffer)
      .resize(192, 192)
      .png()
      .toFile(path.join(__dirname, '../public/icon-192.png'));
    console.log('✓ Generated icon-192.png');
      
    await sharp(svgBuffer)
      .resize(512, 512)
      .png()
      .toFile(path.join(__dirname, '../public/icon-512.png'));
    console.log('✓ Generated icon-512.png');
      
    await sharp(svgBuffer)
      .resize(180, 180)
      .png()
      .toFile(path.join(__dirname, '../public/apple-touch-icon.png'));
    console.log('✓ Generated apple-touch-icon.png');
    
    // Generate favicon.ico (using 32x32 as base)
    await sharp(svgBuffer)
      .resize(32, 32)
      .png()
      .toFile(path.join(__dirname, '../public/favicon.ico'));
    console.log('✓ Generated favicon.ico');
      
    console.log('\n🎉 All favicons generated successfully!');
    console.log('\nGenerated files:');
    console.log('- favicon-16x16.png');
    console.log('- favicon-32x32.png');
    console.log('- favicon.ico');
    console.log('- icon-192.png');
    console.log('- icon-512.png');
    console.log('- apple-touch-icon.png');
    
  } catch (error) {
    console.error('❌ Error generating favicons:', error);
    process.exit(1);
  }
}

generateFavicons();
