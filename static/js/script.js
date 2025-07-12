// Sample product data
const products = [
    {
        id: 1,
        name: "新鮮なトマト",
        price: 350,
        image: "https://placehold.co/400x300/FF5733/FFFFFF?text=Tomato",
        description: "太陽の恵みをたっぷり浴びた、甘くてジューシーな完熟トマトです。サラダやパスタ、煮込み料理に最適です。"
    },
    {
        id: 2,
        name: "有機栽培レタス",
        price: 280,
        image: "https://placehold.co/400x300/33FF57/FFFFFF?text=Lettuce",
        description: "農薬を使わずに育てた、シャキシャキとした食感が特徴の有機栽培レタスです。サンドイッチやサラダにどうぞ。"
    },
    {
        id: 3,
        name: "採れたてキュウリ",
        price: 200,
        image: "https://placehold.co/400x300/3357FF/FFFFFF?text=Cucumber",
        description: "朝採りの新鮮なキュウリです。みずみずしくて歯ごたえがあり、和え物や漬物にぴったりです。"
    },
    {
        id: 4,
        name: "甘みたっぷり玉ねぎ",
        price: 180,
        image: "https://placehold.co/400x300/FFBD33/FFFFFF?text=Onion",
        description: "炒めると甘みが増す、料理の万能選手です。カレーやシチュー、炒め物など幅広く使えます。"
    },
    {
        id: 5,
        name: "ホクホクじゃがいも",
        price: 250,
        image: "https://placehold.co/400x300/8A2BE2/FFFFFF?text=Potato",
        description: "煮崩れしにくく、ホクホクとした食感が楽しめるじゃがいもです。肉じゃがやポテトサラダにおすすめです。"
    },
    {
        id: 6,
        name: "新鮮なほうれん草",
        price: 220,
        image: "https://placehold.co/400x300/20B2AA/FFFFFF?text=Spinach",
        description: "鉄分豊富な新鮮なほうれん草です。おひたしやソテー、スムージーにも最適です。"
    },
    {
        id: 7,
        name: "色鮮やかなパプリカ",
        price: 300,
        image: "https://placehold.co/400x300/FFD700/FFFFFF?text=Paprika",
        description: "赤、黄、オレンジの彩り豊かなパプリカです。生でサラダに、炒め物やグリルにも。"
    },
    {
        id: 8,
        name: "風味豊かなしいたけ",
        price: 400,
        image: "https://placehold.co/400x300/8B4513/FFFFFF?text=Shiitake",
        description: "肉厚で香りの良いしいたけです。鍋物、焼き物、煮物など、和食に欠かせません。"
    }
];

const productGrid = document.getElementById('productGrid');
const searchInput = document.getElementById('searchInput');
const sortSelect = document.getElementById('sortSelect');
const productModal = document.getElementById('productModal');
const modalContent = document.getElementById('modalContent');
const closeModalButton = document.getElementById('closeModal');
const modalImage = document.getElementById('modalImage');
const modalName = document.getElementById('modalName');
const modalPrice = document.getElementById('modalPrice');
const modalDescription = document.getElementById('modalDescription');

let displayedProducts = [...products]; // To hold products after search/sort

// Function to render product cards
function renderProducts(productsToRender) {
    productGrid.innerHTML = ''; // Clear existing products
    productsToRender.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer transform hover:-translate-y-1';
        productCard.innerHTML = `
            <img src="${product.image}" alt="${product.name}" class="w-full h-48 object-cover">
            <div class="p-6">
                <h3 class="text-xl font-semibold text-gray-800 mb-2">${product.name}</h3>
                <p class="text-green-600 text-lg font-bold mb-4">¥${product.price} / 個</p>
                <p class="text-gray-600 text-sm line-clamp-2">${product.description}</p>
                <button class="mt-4 w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-full transition duration-300">
                    詳細を見る
                </button>
            </div>
        `;
        productCard.addEventListener('click', () => openProductModal(product));
        productGrid.appendChild(productCard);
    });
}

// Function to open product detail modal
function openProductModal(product) {
    modalImage.src = product.image;
    modalName.textContent = product.name;
    modalPrice.textContent = `¥${product.price} / 個`;
    modalDescription.textContent = product.description;
    productModal.classList.remove('hidden');
    // Animate modal entry
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 50);
}

// Function to close product detail modal
function closeProductModal() {
    // Animate modal exit
    modalContent.classList.remove('scale-100', 'opacity-100');
    modalContent.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        productModal.classList.add('hidden');
    }, 300); // Match transition duration
}

// Event listener for closing modal
closeModalButton.addEventListener('click', closeProductModal);
productModal.addEventListener('click', (e) => {
    if (e.target === productModal) { // Close only if clicked on backdrop
        closeProductModal();
    }
});

// Function to filter products based on search input
function filterProducts() {
    const searchTerm = searchInput.value.toLowerCase();
    displayedProducts = products.filter(product =>
        product.name.toLowerCase().includes(searchTerm) ||
        product.description.toLowerCase().includes(searchTerm)
    );
    sortProducts(); // Apply sorting after filtering
}

// Function to sort products
function sortProducts() {
    const sortBy = sortSelect.value;
    if (sortBy === 'price-asc') {
        displayedProducts.sort((a, b) => a.price - b.price);
    } else if (sortBy === 'price-desc') {
        displayedProducts.sort((a, b) => b.price - a.price);
    } else if (sortBy === 'name-asc') {
        displayedProducts.sort((a, b) => a.name.localeCompare(b.name, 'ja'));
    } else if (sortBy === 'name-desc') {
        displayedProducts.sort((a, b) => b.name.localeCompare(a.name, 'ja'));
    }
    renderProducts(displayedProducts);
}

// Event listeners for search and sort
searchInput.addEventListener('input', filterProducts);
sortSelect.addEventListener('change', sortProducts);

// Initial render of all products when the page loads
document.addEventListener('DOMContentLoaded', () => {
    renderProducts(products);
});
