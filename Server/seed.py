from config import db, datetime
from models import Product, ProductImage, ProductCategory, Review

def seed_products():
    try:
        # Delete existing products, images, categories, and reviews
        db.session.query(Review).delete()
        db.session.query(ProductCategory).delete()
        db.session.query(ProductImage).delete()
        db.session.query(Product).delete()

        # Add Products
        product1 = Product(name='Product 1', price=100, description='Description of product 1', quantity=10)
        product2 = Product(name='Product 2', price=200, description='Description of product 2', quantity=20)

        db.session.add(product1)
        db.session.add(product2)

        # Add Product Images
        image1 = ProductImage(image_url='http://example.com/image1.jpg', product=product1)
        image2 = ProductImage(image_url='http://example.com/image2.jpg', product=product2)

        db.session.add(image1)
        db.session.add(image2)

        # Add Product Categories
        category1 = ProductCategory(name='Category 1', product=product1)
        category2 = ProductCategory(name='Category 2', product=product2)

        db.session.add(category1)
        db.session.add(category2)

        # Add Reviews
        review1 = Review(product=product1, rating=5, review='Great product!', date=datetime.datetime.utcnow())
        review2 = Review(product=product2, rating=4, review='Good product!', date=datetime.datetime.utcnow())

        db.session.add(review1)
        db.session.add(review2)

        # Commit the changes
        db.session.commit()
        print("Products seeded successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    seed_products()
