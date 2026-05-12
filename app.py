import streamlit as st
import pickle
import requests
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# =========================
# SAFE PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# LOAD MOVIES
# =========================
@st.cache_resource
def load_movies():
    return pickle.load(
        open(os.path.join(BASE_DIR, 'movies.pkl'), 'rb')
    )

movies = load_movies()

# =========================
# BUILD ML MODEL
# =========================
@st.cache_resource
def build_model(data):

    tfidf = TfidfVectorizer(
        stop_words='english'
    )

    vectors = tfidf.fit_transform(
        data['tags']
    )

    model = NearestNeighbors(
        metric='cosine',
        algorithm='brute'
    )

    model.fit(vectors)

    return vectors, model

vectors, model = build_model(movies)

# =========================
# TMDB API KEY
# =========================
API_KEY = "9c76ec7ba8f1bb21e952c470abc6f7db"

# =========================
# FETCH MOVIE POSTER
# =========================
@st.cache_data(show_spinner=False)
def fetch_poster(movie_title):

    try:

        url = (
            f"https://api.themoviedb.org/3/search/movie"
            f"?api_key={API_KEY}&query={movie_title}"
        )

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        if data['results']:

            poster_path = data['results'][0].get(
                'poster_path'
            )

            if poster_path:

                return (
                    "https://image.tmdb.org/t/p/w500"
                    + poster_path
                )

        return "https://via.placeholder.com/500x750?text=No+Image"

    except:

        return "https://via.placeholder.com/500x750?text=Error"

# =========================
# RECOMMEND FUNCTION
# =========================
def recommend(movie, n=10):

    # exact match
    match = movies[
        movies['title'].str.lower() == movie.lower()
    ]

    # partial match fallback
    if len(match) == 0:

        match = movies[
            movies['title'].str.contains(
                movie,
                case=False,
                na=False
            )
        ]

    # movie not found
    if len(match) == 0:
        return None

    movie_title = match.iloc[0]['title']
    movie_index = match.index[0]

    distances, indices = model.kneighbors(
        vectors[movie_index],
        n_neighbors=n + 1
    )

    recommended_movies = []
    recommended_posters = []
    recommended_scores = []

    for idx, dist in zip(
        indices[0][1:],
        distances[0][1:]
    ):

        title = movies.iloc[idx].title

        recommended_movies.append(title)

        recommended_posters.append(
            fetch_poster(title)
        )

        # convert cosine distance -> similarity
        recommended_scores.append(
            round(1 - dist, 2)
        )

    return (
        movie_title,
        recommended_movies,
        recommended_posters,
        recommended_scores
    )

# =========================
# HEADER
# =========================
st.markdown("""
<h1 style='text-align:center; color:#E50914;'>
🍿 Movie Recommendation System
</h1>

<h4 style='text-align:center; color:gray;'>
Netflix Style ML Project 🎬
</h4>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🎯 About Project")

st.sidebar.info("""
This AI recommender suggests movies using:

✔ Genres  
✔ Keywords  
✔ Cast  
✔ Crew  

Built with:
- Streamlit
- Scikit-learn
- TF-IDF
- Nearest Neighbors
- TMDB API
""")

# =========================
# MOVIE SELECT BOX
# =========================
movie_list = movies['title'].values

selected_movie = st.selectbox(
    "🎥 Select a movie:",
    sorted(movie_list)
)

# =========================
# NUMBER OF RECOMMENDATIONS
# =========================
num_recommendations = st.slider(
    "📌 Number of recommendations",
    5,
    20,
    10
)

# =========================
# RECOMMEND BUTTON
# =========================
if st.button("🎬 Recommend"):

    with st.spinner(
        "Finding best movies for you... 🍿"
    ):

        result = recommend(
            selected_movie,
            num_recommendations
        )

    if result is None:

        st.error(
            "Movie not found 😢"
        )

    else:

        (
            movie_name,
            names,
            posters,
            scores
        ) = result

        st.subheader(
            f"Because you liked: 🎬 {movie_name}"
        )

        # =========================
        # DISPLAY MOVIES
        # =========================
        for i in range(0, len(names), 5):

            cols = st.columns(5)

            for j in range(5):

                if i + j < len(names):

                    with cols[j]:

                        st.image(
                            posters[i + j],
                            use_container_width=True
                        )

                        st.markdown(
                            f"""
                            <div style='text-align:center'>

                            <h4>
                            {names[i + j]}
                            </h4>

                            ⭐ Similarity:
                            {scores[i + j]}

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>

img {
    border-radius: 15px;
}

.stButton>button {

    width: 100%;
    background-color: #E50914;
    color: white;

    border-radius: 10px;

    height: 3em;

    font-size: 18px;

    border: none;
}

.stButton>button:hover {

    background-color: #b20710;
    color: white;
}

</style>
""", unsafe_allow_html=True)