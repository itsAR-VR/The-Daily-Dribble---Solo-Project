import pandas as pd

# Create test data
data = {
    'platform': ['hubx', 'gsmexchange', 'kardof'],
    'product_name': ['iPhone 14 Pro', 'Samsung Galaxy S23', 'Google Pixel 7'],
    'condition': ['New', 'Used', 'New'],
    'quantity': [5, 3, 2],
    'price': [999, 750, 650]
}

df = pd.DataFrame(data)
df.to_excel('test_listing.xlsx', index=False)
print("Test file created: test_listing.xlsx") 