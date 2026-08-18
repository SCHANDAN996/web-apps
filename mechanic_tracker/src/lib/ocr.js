/**
 * 100% Free Client-Side OCR using Tesseract.js
 * Extracts core fee, vendor, date from receipt photos directly in the browser.
 */

import { createWorker } from 'tesseract.js';

export async function parseReceipt(imageFile) {
  try {
    // We create a worker with 'eng' language
    const worker = await createWorker('eng');

    // Preprocess image to enhance OCR accuracy (Canvas API)
    const processedUrl = await preprocessImage(imageFile);
    
    // Recognize text
    const { data } = await worker.recognize(processedUrl);
    
    // Extract required data
    const extracted = extractCoreData(data.text);
    
    // Cleanup
    await worker.terminate();
    URL.revokeObjectURL(processedUrl);
    
    return { success: true, raw: data.text, extracted };
  } catch (err) {
    return { success: false, error: err.message || 'Local OCR failed' };
  }
}

// Optional preprocessing to improve Tesseract accuracy
async function preprocessImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const objUrl = URL.createObjectURL(file);
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      // Scale down if image is too large to prevent out-of-memory errors
      const MAX_WIDTH = 1200;
      let width = img.width;
      let height = img.height;
      if (width > MAX_WIDTH) {
        height = Math.round((height * MAX_WIDTH) / width);
        width = MAX_WIDTH;
      }

      canvas.width = width;
      canvas.height = height;
      
      // Apply grayscale and contrast using context filter
      ctx.filter = 'grayscale(100%) contrast(150%) brightness(110%)';
      ctx.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob((blob) => {
        URL.revokeObjectURL(objUrl);
        if (blob) {
          resolve(URL.createObjectURL(blob));
        } else {
          resolve(objUrl); // fallback
        }
      }, 'image/jpeg', 0.9);
    };
    img.onerror = () => resolve(objUrl); // fallback if error
    img.src = objUrl;
  });
}

function extractCoreData(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const result = { vendor: '', date: '', coreItems: [], totalCoreFee: 0 };

  // Vendor: first non-empty line that looks like a name
  if (lines.length > 0) {
    result.vendor = lines[0].replace(/[^a-zA-Z0-9\s&'.-]/g, '').trim();
  }

  // Date patterns
  const datePatterns = [
    /(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})/,
    /(\w{3,9}\s+\d{1,2},?\s+\d{4})/i,
  ];
  for (const line of lines) {
    for (const pat of datePatterns) {
      const m = line.match(pat);
      if (m) { result.date = m[1]; break; }
    }
    if (result.date) break;
  }

  // Core fee lines
  const corePat = /\b(core|deposit|cor\s*dep|core\s*charge|core\s*fee)\b/i;
  // Match amounts like 50.00, $50.00, or 50
  const amountPat = /(?:[$£€₹]?)\s*(\d+\.?\d{0,2})/;
  
  for (const line of lines) {
    if (corePat.test(line)) {
      const amtMatch = line.match(amountPat);
      const amount = amtMatch ? parseFloat(amtMatch[1]) : 0;
      if (amount > 0) {
        result.coreItems.push({ line, amount });
        result.totalCoreFee += amount;
      }
    }
  }

  return result;
}
