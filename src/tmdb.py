from src.config import TMDB_API_KEY


class MovieData:
    def __init__(self,year=2024,overview="",name="",categories="",providers="",
                 vote_average=0,vote_count=0,similar_movies=""):

        self.year=year
        self.overview=overview
        self.name=name
        self.categories=categories
        self.providers=providers
        self.vote_average=vote_average
        self.vote_count=vote_count
        self.similar_movies=similar_movies

import os

import requests

from tmdbv3api import TMDb
from tmdbv3api import Movie

poster_folder = "MoviePosters"
logo_folder = "ProviderLogos"

folders = [poster_folder,logo_folder]

for folder in folders:
    if not os.path.exists(folder):
        os.mkdir(folder)


api_key = TMDB_API_KEY

base_url = 'https://api.themoviedb.org/3'

poster_base_url = "https://image.tmdb.org/t/p/w500"

# TMDb nesnesi oluşturma ve API anahtarını ekleme
tmdb = TMDb()

tmdb.api_key = api_key

tmdb.language = 'tr'

# Movie nesnesi oluşturma
movie = Movie()

movie_data = MovieData()

similar_movie_count = 5 # benzer kaç film gösterilsin.

def find_movie_id(movie_name,is_detail=False,is_add = False):
    search_results = movie.search(movie_name)
    try:
        first_result = search_results[0]
        movie_id = first_result.id
        
        if is_add: # film ekleme ekranı için.
            get_simple_data(movie_id)
            
        elif is_detail: # film detay sayfasında görüntülemek için.
            get_more_details(movie_id)
            get_movie_poster(movie_id, movie_name)
            get_provider_data(movie_id)
    except TypeError:
        print("Bulunamadı!")

    return movie_data

def get_simple_data(movie_id):
    movie_details = movie.details(movie_id) # detaylar için :

    movie_data.name = movie_details.original_title # filmin adı
    
    categories = list()
    for category in movie_details.genres: # kategorileri
        categories.append(category.name)

    if categories == []:
        categories = ["diğer"]

    movie_data.categories = categories

    movie_data.year = movie_details.release_date[:4] # yayın tarihi

def get_more_details(movie_id):
    similar_movies = list()
    search_similar = movie.similar(movie_id)
    num_result = search_similar.total_results

    for counter ,similar_movie in enumerate(search_similar): #benzer filmleri bul.
        if num_result == counter:
            break
        similar_movies.append((similar_movie.original_title,similar_movie.release_date[:4]))  # yalnızca isim bilgileri alınıyor.
        if len(similar_movies) == similar_movie_count: # en çok benzeyen üç filmi al.
            break

    movie_data.similar_movies = similar_movies

    movie_details = movie.details(movie_id) # detaylar için :

    movie_data.vote_average = movie_details.vote_average #ortalama puanı
    movie_data.vote_count = movie_details.vote_count # oy sayısı
    movie_data.overview = movie_details.overview  # özeti


def get_provider_data(movie_id):
    providers = movie.watch_providers(movie_id)  # yayınlayan platformlar

    def download_logo(platform_name,logo_path):
        img_name = f"{platform_name}.png".lower()

        img_file = os.path.join(logo_folder, img_name)
        if os.path.isfile(img_file):
            print(f"{platform_name} zaten kayıtlı.")
        else:
            full_path = "https://www.themoviedb.org/t/p/original" + logo_path
            try:
                response = requests.get(full_path)

                if response.status_code == 200:
                    with open(img_file, "wb") as f:
                        f.write(response.content)
                        print(f"{img_name} indirildi.")
                else:
                    print(f"sunucu hatası")
            except:
                print("bağlantı hatası")


    provider_list = list()
    for result in providers["results"]:
        if result.get("results") == 'TR':
            for option in result:
                for i in option:
                    if type(i) != str:
                        platform_name = i.get("provider_name")
                        platform_path = i.get("logo_path")

                        download_logo(platform_name,platform_path)

                        if not platform_name in provider_list:
                            provider_list.append(platform_name)

    movie_data.providers = provider_list


def get_movie_poster(movie_id,movie_name):
    url = f'{base_url}/movie/{movie_id}?api_key={api_key}&language=tr'

    response = requests.get(url)

    if response.status_code == 200:
        poster_path = response.json().get('poster_path')

        poster_url = poster_base_url + poster_path

        download_poster(movie_name,poster_url)


def download_poster(movie_name,poster_url):
    poster_name = movie_name.lower()
    poster_name = poster_name.replace(' ', '_') + ".jpg"
    poster_path = os.path.join(poster_folder, poster_name)
    if os.path.isfile(poster_path):
        print(f"{poster_name} zaten kayıtlı")
        return

    response = requests.get(poster_url)

    if response.status_code == 200:
        try:
            with open(poster_path, 'wb') as file:
                file.write(response.content)
        except FileNotFoundError:
            pass
        print(f"Poster kaydedildi: {poster_name}")

        return

    print("Poster indirilemedi.")