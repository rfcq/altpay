let stream = null;
let scanningInterval = null;

// Handle product form submission
document.getElementById('productForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('productName').value.trim();
    const price = parseFloat(document.getElementById('productPrice').value);
    
    if (!name || isNaN(price) || price <= 0) {
        alert('Please enter a valid name and price.');
        return;
    }
    
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, price }),
        });
        
        if (response.ok) {
            const product = await response.json();
            location.reload(); // Reload to show new product
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add product');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to add product');
    }
    
    document.getElementById('productForm').reset();
});

// Add to cart from product list
async function addToCartFromList(productId) {
    try {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ product_id: productId }),
        });
        
        if (response.ok) {
            const data = await response.json();
            location.reload(); // Reload to update cart
        } else {
            alert('Failed to add to cart');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to add to cart');
    }
}

// Open QR scanner
function openScanner() {
    const modal = document.getElementById('scannerModal');
    modal.classList.add('active');
    
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    
    navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } // Use back camera on mobile
    })
    .then((mediaStream) => {
        stream = mediaStream;
        video.srcObject = stream;
        video.play();
        
        scanningInterval = setInterval(() => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height);
                
                if (code) {
                    handleScannedQR(code.data);
                }
            }
        }, 100);
    })
    .catch((error) => {
        console.error('Error accessing camera:', error);
        document.getElementById('scannerStatus').textContent = 
            'Camera access denied. Please allow camera permissions.';
    });
}

// Close QR scanner
function closeScanner() {
    const modal = document.getElementById('scannerModal');
    modal.classList.remove('active');
    
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
    }
    
    const video = document.getElementById('video');
    video.srcObject = null;
    document.getElementById('scannerStatus').textContent = 'Point camera at QR code...';
}

// Handle scanned QR code
async function handleScannedQR(qrData) {
    try {
        const data = JSON.parse(qrData);
        
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`Added to cart: ${data.name} - $${data.price.toFixed(2)}`);
            closeScanner();
            location.reload(); // Reload to update cart
        } else {
            alert('Failed to add to cart');
        }
    } catch (error) {
        console.error('Error parsing QR code:', error);
        alert('Invalid QR code format');
    }
}

// Close modal when clicking outside
document.getElementById('scannerModal').addEventListener('click', (e) => {
    if (e.target.id === 'scannerModal') {
        closeScanner();
    }
});
