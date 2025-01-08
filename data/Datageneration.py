import uuid
import random
import pandas as pd

# Define post types and engagement biases
post_types = ['Carousel', 'Reel', 'Static']
data_ranges = {
    'Carousel': {'likes': (1000, 4000), 'shares': (150, 450), 'comments': (30, 300)},
    'Reel': {'likes': (3000, 7000), 'shares': (300, 1000), 'comments': (50, 900)},
    'Static': {'likes': (500, 2500), 'shares': (10, 100), 'comments': (5, 300)}
}

# Generate data
data = []
for _ in range(300):
    post_id = str(uuid.uuid4())
    post_type = random.choices(post_types, weights=[35, 45, 20], k=1)[0]  # Bias: Carousel & Reel are more frequent
    likes = random.randint(*data_ranges[post_type]['likes'])
    shares = random.randint(*data_ranges[post_type]['shares'])
    comments = random.randint(*data_ranges[post_type]['comments'])

    # Ensure views are greater than the sum of likes, shares, and comments
    min_views = max(likes , shares , comments ) + 1
    max_views = min_views + random.randint(100, 5000)  # Add some variability to the views
    views = random.randint(min_views, max_views)

    data.append([post_id, post_type, views , likes, shares, comments])

# Create DataFrame
columns = ['Post_ID', 'Post_Type', 'Views' , 'Likes', 'Shares', 'Comments']
df = pd.DataFrame(data, columns=columns)

# Save dataset to CSV and JSON
df.to_csv('mock_social_media_data.csv', index=False)
# df.to_json('mock_social_media_data.json', orient='records', date_format='iso')

print("Mock dataset created with 300 samples, including views.")
