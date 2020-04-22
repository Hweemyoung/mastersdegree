from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader

if __name__ == '__main__':
    preprocessor = Preprocessor()
    items = {'snippet': {'title': 'Ray Kurzweil - The Age of Spiritual Machines - The Future of The 21st Century', 'tags': ['singularity', 'ai', 'artificial intelligence', 'deep learning', 'machine learning', 'deepmind', 'robots', 'robotics', 'self-driving cars', 'driverless cars', 'Ray Kurzweil'], 'channelTitle': 'The Artificial Intelligence Channel', 'publishedAt': '2018-07-01T17:16:05.000Z', 'description': 'Recorded January 21st, 1999\nRay Kurzweil spoke about his book The Age of Spiritual Machines about artificial intelligence and the future course of humanity. First published in hardcover on January 1, 1999 by Viking, it has received attention from The New York Times, The New York Review of Books and The Atlantic. In the book Kurzweil outlines his vision for how technology will progress during the 21st century.', 'channelId': 'UC5g-f-g4EVRkqL8Xs888BLA', 'defaultAudioLanguage': 'en'}, 'statistics': {'dislikeCount': '10', 'likeCount': '112', 'favoriteCount': '0', 'commentCount': '16', 'viewCount': '4824'}, 'contentDetails': {'duration': 'PT1H18M55S'}}
    print(preprocessor.preprocess(items))
