exports.productSchema = {
    id: "PRD001",
    name: "Royal Linen Shirt",
    brand: "Kavachi",
    category: "Shirt",
    gender: "Men",
    skinToneRecommended: ["Fair", "Medium"],
    color: ["Beige", "White"],
    hexColor: ["#F5F5DC", "#FFFFFF"],
    size: ["S", "M", "L", "XL"],
    price: 2499,
    discountPrice: 1999,
    currency: "INR",
    fabric: "Linen",
    clothType: "Casual",
    fit: "Slim Fit",
    pattern: "Solid",
    madeIn: "India",
    season: "Summer",
    stock: 50,
    rating: 4.5,
    reviewsCount: 124,
    images: [
        "https://example.com/images/shirt1.jpg",
        "https://example.com/images/shirt2.jpg"
    ],
    description: "Premium breathable linen shirt for summer.",
    createdAt: new Date().toISOString()
};

exports.userSchema = {
    id: "firebase_uid",
    name: "John Doe",
    email: "john@example.com",
    gender: "Men",
    savedAddresses: [
        {
            id: "addr1",
            street: "123 Luxury Ave",
            city: "Mumbai",
            state: "MH",
            zip: "400001",
            country: "India",
            isDefault: true
        }
    ],
    orderHistory: ["ORD1234"],
    wishlist: ["PRD001"],
    createdAt: new Date().toISOString()
};

exports.orderSchema = {
    id: "ORD1234",
    userId: "firebase_uid",
    items: [
        {
            productId: "PRD001",
            quantity: 1,
            size: "M",
            color: "Beige",
            price: 1999
        }
    ],
    totalAmount: 1999,
    paymentMethod: "Razorpay",
    address: "addr1",
    status: "Processing",
    orderDate: new Date().toISOString(),
    expectedDeliveryDate: new Date(new Date().setDate(new Date().getDate() + 5)).toISOString()
};
