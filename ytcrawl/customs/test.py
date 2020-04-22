from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader

if __name__ == '__main__':
    items = {
        "snippet": {
            "publishedAt": "2016-01-21T15:34:28.000Z"
        },
        "statistics": {
            "viewCount": "19630682",
            "commentCount": "0",
            "subscriberCount": "191000",
            "videoCount": "120"
        },
        "brandingSettings": {
            "channel": {
                "title": "DeepMind",
                "description": "Artificial intelligence could be one of humanity's most useful inventions. DeepMind aims to build advanced AI to expand our knowledge and find new answers. By solving this one thing, we believe we could help people solve thousands of problems.\n\nWe’re a team of scientists, engineers, machine learning experts and more, working together to advance the state of the art in artificial intelligence. We use our technologies for widespread public benefit and scientific discovery, and collaborate with others on critical challenges, ensuring safety and ethics are the highest priority.\n\nWe have a track record of breakthroughs in fundamental AI research, published in journals like Nature, Science, and more. Our programs have learned to diagnose eye diseases as effectively as the world’s top doctors, to save 30% of the energy used to keep data centres cool, and to predict the complex 3D shapes of proteins - which could one day transform how drugs are invented. \n\nFind out more: deepmind.com",
                "country": "GB"
            }
        }
    }
    db_chan = DBChannelsUploader()
    db_chan.insert('channels', items)
