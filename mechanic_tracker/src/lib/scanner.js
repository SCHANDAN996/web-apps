/**
 * Barcode scanner — BarcodeDetector API with Quagga2 fallback
 */

let scannerActive = false;
let stream = null;

export async function startBarcodeScanner(onDetected, onClose) {
  if (scannerActive) return;
  scannerActive = true;

  // Create scanner UI
  const container = document.createElement('div');
  container.className = 'scanner-container';
  container.innerHTML = `
    <button class="scanner-close" id="scanner-close-btn">✕</button>
    <video class="scanner-video" id="scanner-video" autoplay playsinline></video>
    <div class="scanner-overlay">
      <div class="scanner-frame"></div>
    </div>
    <div class="scanner-hint">Point camera at barcode</div>
  `;
  document.body.appendChild(container);

  const video = container.querySelector('#scanner-video');
  const closeBtn = container.querySelector('#scanner-close-btn');

  const cleanup = () => {
    scannerActive = false;
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    container.remove();
    if (onClose) onClose();
  };

  closeBtn.addEventListener('click', cleanup);

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    video.srcObject = stream;
    await video.play();

    // Try native BarcodeDetector first
    if ('BarcodeDetector' in window) {
      const detector = new BarcodeDetector({
        formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39']
      });
      const scanFrame = async () => {
        if (!scannerActive) return;
        try {
          const barcodes = await detector.detect(video);
          if (barcodes.length > 0) {
            onDetected(barcodes[0].rawValue);
            cleanup();
            return;
          }
        } catch (e) { /* continue scanning */ }
        requestAnimationFrame(scanFrame);
      };
      scanFrame();
    } else {
      // Fallback: Quagga2
      const Quagga = (await import('@ericblade/quagga2')).default;
      // Quagga needs a canvas from the video
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 640; canvas.height = 480;

      const scanLoop = () => {
        if (!scannerActive) return;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        Quagga.decodeSingle({
          src: canvas.toDataURL('image/jpeg'),
          numOfWorkers: 0,
          decoder: { readers: ['ean_reader', 'upc_reader', 'code_128_reader'] }
        }, (result) => {
          if (result?.codeResult?.code) {
            onDetected(result.codeResult.code);
            cleanup();
          } else {
            setTimeout(scanLoop, 500);
          }
        });
      };
      scanLoop();
    }
  } catch (err) {
    cleanup();
    throw new Error('Camera access denied or not available');
  }
}
