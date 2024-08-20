import sys

sys.path.append("..")
sys.path.append("spiders/")

import urllib.parse
import scrapy
from datetime import datetime
import ingestion_item as ii
import uuid
import json
import re

class IGNSanskrit(scrapy.Spider):
    name = 'IGNSanskrit'
    start_urls = ['https://ignca.gov.in/online-digital-resources/gaudiya-grantha-mandira-sanskrit-text-repository/']


    def parse(self, response):

        summaries = {
        'ALANKARA': 'The Alankara Shastra is a traditional Indian science of aesthetics that deals with the principles and techniques of literary composition and ornamentation.It is an important aspect of Indian literary criticism and aims to enhance the beauty and expressiveness of literary works.',

        'BHAGAVAD GITA': 'The Bhagavad Gita is a 700-verse Hindu scripture that forms a part of the ancient Indian epic, the Mahabharata.It consists of a conversation between Prince Arjuna and the god Krishna, who serves as his charioteer.The Gita addresses the ethical and philosophical dilemmas faced by Arjuna on the battlefield and provides profound insights into life, duty, and spirituality.',

        'BHAKTI-RASA': 'Bhakti-rasa refers to the devotional or emotional aspect of bhakti, which is the path of love and devotion in Hinduism.It is a profound and intimate connection between the devotee and the divine, characterized by intense emotions and feelings of love, surrender, and longing.',

        'CARITAMRITA': 'The Caritamrita is a sacred scripture in the Gaudiya Vaishnavism tradition, which worships Lord Krishna as the Supreme Personality of Godhead.It is considered one of the most important and comprehensive biographies of the 15th-century saint and spiritual leader, Sri Chaitanya Mahaprabhu.',

        'CHANDAS': 'Chandas is a term used in Sanskrit literature to refer to the science of meter and poetic composition.It encompasses the rules and structures that govern the rhythm, meter, and syllabic patterns in traditional Indian poetry.Chandas is an essential aspect of classical Indian literature, including the Vedas, epics like the Ramayana and Mahabharata, and various poetic works.',

        'DARSANA': 'Darsana is a Sanskrit term that refers to the Indian philosophical systems or schools of thought.It is derived from the root word "dṛś," meaning "to see" or "to perceive," and it signifies the act of gaining insight or understanding through direct perception or observation.Darsana encompasses various philosophical traditions in India, each offering a unique perspective on reality, existence, and the nature of consciousness.',

        'KAMA-SASTRA': 'The Kama-sastra, also known as the Kama Sutra, is an ancient Indian text attributed to Vatsyayana.It is a comprehensive treatise on the art of love, sexuality, and sensual pleasure.Written in Sanskrit, the Kama-sastra consists of seven books that explore various aspects of human relationships, including courtship, marriage, and sexual practices.',

        'NATAKA': 'Nataka is a Sanskrit term that refers to a dramatic play or a theatrical performance in traditional Indian literature.It is one of the major genres of classical Indian drama, along with other forms such as Prakarana, Bhana, and Rupaka.Nataka plays typically follow a structured format and convey complex narratives, often drawing inspiration from mythological stories, historical events, or social themes.',

        'PURANA': 'The Puranas are a collection of ancient Hindu texts that contain mythological and historical narratives, genealogies, cosmology, philosophy, and religious teachings.They are considered an important part of Hindu scripture and provide valuable insights into the mythology, legends, and cultural heritage of ancient India.',

        'KAVYA': 'Kavya is a Sanskrit literary style that originated in India around 200 BCE and flourished until 1200 CE. It is characterized by the use of elaborate figures of speech, such as metaphors, similes, and hyperbole, to create a rich and evocative emotional effect. Kavya can refer to both poetry and prose, and it includes a wide variety of genres, such as epics, courtly romances, and lyric poems.',

        'SANGITA': 'Sangita, also spelled as Sangeeta, is a term that encompasses the arts of music, dance, and drama in traditional Indian culture.It is a comprehensive term that signifies the integration of these performing arts into a harmonious and aesthetic expression.',

        'SMRITI': 'Smriti, in Hinduism, refers to the body of religious texts that are derived from human memory and are considered secondary in authority to the Shruti texts (the Vedas).Smriti literature consists of a wide range of texts including the Dharmashastras (legal and ethical codes), the Itihasas (epics such as the Mahabharata and Ramayana), the Puranas (mythological and genealogical narratives), and the Agamas (ritual and philosophical treatises).',

        'STOTRA': 'Stotra refers to a hymn, prayer, or devotional composition that is dedicated to praising and glorifying a deity or a revered figure in Hinduism.Stotras are an integral part of devotional practices and are recited or sung as a means of expressing reverence, devotion, and gratitude towards the divine.',

        'SUBHASITA': 'Subhashita refers to a wise, well-expressed, or auspicious saying.It is a form of traditional Indian literature consisting of concise verses or phrases that convey profound wisdom, moral values, or practical advice.Subhashitas are often presented in the form of a couplet or a short verse, and they cover a wide range of subjects including ethics, social conduct, philosophy, spirituality, and human nature.',

        'TANTRA AND PANCARATRA': 'Tantra is a Sanskrit term that refers to a diverse set of esoteric and ritualistic practices aimed at spiritual growth, self-realization, and union with the divine.The term "Tantra" means "loom" or "weave," suggesting the interwoven nature of the physical and spiritual realms.Tantra encompasses a wide range of practices, including meditation, ritual worship, mantra recitation, visualization, and the use of yantras (sacred diagrams) and mudras (gestures). Pancharatra is a Sanskrit term that refers to a specific school of Vaishnavism, focusing on devotion to Lord Vishnu and his avatars, particularly Krishna.The term "Pancharatra" means "five nights" or "five divisions," indicating its origin as a body of teachings revealed during five nights to the sage Narada.',

        'UPANISAD': 'Upanisad refers to a collection of ancient philosophical and spiritual texts that form the concluding portions of the Vedic scriptures, known as the Vedas.The Upanishads are considered the foundation of Vedanta philosophy and are highly revered in Hinduism.',

        'VYAKARANA': 'The Sanskrit term "Vyakarana" refers to the field of grammar in the Indian linguistic tradition.It is the study of the rules and principles governing the structure, formation, and usage of language.Vyakarana plays a crucial role in preserving and analyzing the grammar of Sanskrit, which is known for its intricacy and precision.',

        'YOGA': 'There are several important Sanskrit texts that form the foundation of the yogic tradition and provide guidance on various aspects of yoga practice, philosophy, and spirituality.These texts elucidate the principles, techniques, and goals of yoga, offering profound insights into the nature of existence and the path to self-realization.'
        }
        i = 0
        ingestion_items = []
        series_list = []
        topic_list = []
        second_list = []
        current_series = ''
        current_topic = ''
        second_topic = ''
        series_done = -1
        topic_done = -1
        second_done = -1
        skip_first = True

        for row in response.css("table.tablepress tbody tr"):
            if row.css("td strong::text").get() != None:
                series_list.append(row.css("td strong::text").get())

        topic_list = response.css('td[align="right"]::text').getall()

        for row in response.css("table.tablepress tbody tr"):
            if row.css("td i::text").get() != None:
                second_list.append(row.css("td i::text").get())

        for row in response.css("table.tablepress tbody tr"):
            if skip_first == True:
                skip_first = False
                continue
            if i == len(response.css("table.tablepress tbody tr")) - 2:
                return ingestion_items
            small_list = []
           # if (row.css("td i::text").get() == None):
           #     if row.css("td::text").getall() != ['SMRITI']:
            small_list.append(row.css("td a::text").get())
            for item in row.css("td::text").getall():
                small_list.append(item)
            small_list.append(urllib.parse.urljoin("https://ignca.gov.in/", row.css("td a::attr(href)").get()))



            if small_list[0] == None or small_list[1] in topic_list:
                # print(series_done+1)
                # current_series = series_list[series_done + 1]
                # series_done += 1
                if row.css("td strong::text").get() != None:
                    current_series = series_list[series_done + 1]
                    series_done += 1
                    current_topic = ''
                    second_topic = ''
                if row.css("td i::text").get() != None:
                    second_topic = second_list[second_done + 1]
                    second_done += 1
                if len(small_list) > 5:
                    current_topic = small_list[1]
                    small_list.remove(current_topic)
                    #topic_done += 1
                    if current_topic == 'Other' or current_topic == 'Others':
                        current_topic = ''
                    ingestion_item = ii.IngestionItem()
                    collection_item = ii.CollectionItem()
                    harvest_item = ii.HarvestItem()
                    file_item = ii.FileItem()
                    prop_item = ii.PropItem()
                    artifact_item = ii.ArtifactItem()
                    thumbnail_item = ii.ThumbnailItem()
                    author_item = ii.AuthorItem()
                    # Harvest Items
                    harvest_item["id"] = str(uuid.uuid4())
                    harvest_item["date"] = datetime.now()
                    # Collection Item
                    collection_item["title"] = 'Sanskrit Text Repository'
                    collection_item["id"] = '88657b24-beb8-464d-b239-e99cfc05a6ff'
                    collection_item["organization"] = 'indira-gandhi-national-centre-for-the-arts'
                    # ID and Publisher
                    artifact_item['id'] = str(uuid.uuid4())
                    # File Item
                    file_item = ii.FileItem()
                    file_item["url"] = small_list[-1]
                    file_item["media_type"] = "application/pdf"
                    file_item['language'] = "sa"
                    artifact_item["files"] = [file_item]
                    # Author
                    title_obj = ''
                    author_obj = ''
                    input_string = small_list[0]
                    if input_string.count("::") >= 2:
                        title_obj, author_obj = input_string.split("::", 2)[1:3]
                    else:
                        if "::" in input_string:
                            title_obj, author_obj = input_string.split("::", 1)
                        else:
                            title_obj = input_string
                            author_obj = ""
                    title_obj = title_obj.strip()
                    author_obj = author_obj.strip()
                    if author_obj in ["Agni Purana", "Introduction", "Root Text", "4 commentaries", "Searchable",
                                      "Cantos 01-12", "Cantos 01-02", "Cantos 03-04", "Cantos 05-06"]:
                        author_obj = ""
                        title_obj = small_list[0]
                    if current_topic == "Gopala Campu":
                        author_obj = ""
                        title_obj = small_list[0]
                    if author_obj != '':
                        author_item["name"] = author_obj
                        artifact_item["authors"] = [author_item]
                    # Series Info
                    artifact_item["title"] = title_obj
                    artifact_item["series"] = current_series.title()
                    artifact_item["summary"] = summaries[current_series]
                    artifact_item["languages"] = ["sa"]
                    # Page Number
                    prop_item['key'] = "Pages"
                    prop_item['value'] = int(small_list[2])
                    artifact_item['props'] = [prop_item]
                    # Topic
                    topics_list = []
                    temp_topics = []
                    if current_topic != '':
                        if ',' in current_topic:
                            temp_topics = current_topic.split(',')
                            for item in temp_topics:
                                topics_list.append(item.title().strip())
                        else:
                            topics_list.append(current_topic.title())
                    if second_topic != '':
                        topics_list.append(second_topic.title())
                    if topics_list != []:
                        artifact_item["topics"] = topics_list

                    ingestion_item["collection"] = collection_item
                    ingestion_item["harvest"] = harvest_item
                    ingestion_item["artifacts"] = [artifact_item]

                    ingestion_items.append(ingestion_item)
                i += 1
            else:
                # Declare Items
                ingestion_item = ii.IngestionItem()
                collection_item = ii.CollectionItem()
                harvest_item = ii.HarvestItem()
                file_item = ii.FileItem()
                prop_item = ii.PropItem()
                artifact_item = ii.ArtifactItem()
                thumbnail_item = ii.ThumbnailItem()
                author_item = ii.AuthorItem()
                # Harvest Items
                harvest_item["id"] = str(uuid.uuid4())
                harvest_item["date"] = datetime.now()
                # Collection Item
                collection_item["title"] = 'Sanskrit Text Repository'
                collection_item["id"] = '88657b24-beb8-464d-b239-e99cfc05a6ff'
                collection_item["organization"] = 'indira-gandhi-national-centre-for-the-arts'
                # ID and Publisher
                artifact_item['id'] = str(uuid.uuid4())
                # File Item
                file_item = ii.FileItem()
                file_item["url"] = small_list[-1]
                file_item["media_type"] = "application/pdf"
                file_item['language'] = "sa"
                artifact_item["files"] = [file_item]
                # Author
                title_obj = ''
                author_obj = ''
                input_string = small_list[0]
                if input_string.count("::") >= 2:
                    title_obj, author_obj = input_string.split("::", 2)[1:3]
                else:
                    if "::" in input_string:
                        title_obj, author_obj = input_string.split("::", 1)
                    else:
                        title_obj = input_string
                        author_obj = ""
                title_obj = title_obj.strip()
                author_obj = author_obj.strip()
                if author_obj in ["Agni Purana", "Introduction", "Root Text", "4 commentaries", "Searchable",
                              "Cantos 01-12", "Cantos 01-02", "Cantos 03-04", "Cantos 05-06"]:
                    author_obj = ""
                    title_obj = small_list[0]
                if current_topic == "Gopala Campu":
                    author_obj = ""
                    title_obj = small_list[0]
                if author_obj != '':
                    author_item["name"] = author_obj
                    artifact_item["authors"] = [author_item]
                # Series Info
                artifact_item["title"] = title_obj
                artifact_item["series"] = current_series.title()
                artifact_item["summary"] = summaries[current_series]
                artifact_item["languages"] = ["sa"]
                # Page Number
                prop_item['key'] = "Pages"
                prop_item['value'] = int(small_list[2])
                artifact_item['props'] = [prop_item]
                # Topic
                topics_list = []
                temp_topics = []
                if current_topic != '':
                    if ',' in current_topic:
                        temp_topics = current_topic.split(',')
                        for item in temp_topics:
                            topics_list.append(item.title())
                    else:
                        topics_list.append(current_topic.title())
                if second_topic != '':
                    topics_list.append(second_topic.title())
                if topics_list != []:
                    artifact_item["topics"] = topics_list

                ingestion_item["collection"] = collection_item
                ingestion_item["harvest"] = harvest_item
                ingestion_item["artifacts"] = [artifact_item]

                ingestion_items.append(ingestion_item)
                i += 1
