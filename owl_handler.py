from rdflib import Graph

NS = "http://www.semanticweb.org/chris/ontologies/2026/3/"


class MovieOntology:
    def __init__(self, owl_file: str):
        print(f"Load ontology from {owl_file}...")
        self.g = Graph()
        self.g.parse(owl_file)
        print(f"Loaded! ({len(self.g)} triples)")

    def get_all_movies(self, limit: int = 5) -> list[dict]:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?title ?year ?rating (GROUP_CONCAT(?genre; separator=", ") AS ?genres)
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasGenre ?genre .
        }}
        GROUP BY ?title ?year ?rating
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "genres"])

    def search_by_genre(self, genre: str, limit: int = 5) -> list[dict]:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?title ?year ?rating (GROUP_CONCAT(?g; separator=", ") AS ?genres)
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasGenre ?g .
            ?movie ex:hasGenre ?filterGenre .
            FILTER(LCASE(STR(?filterGenre)) = "{genre.lower()}")
        }}
        GROUP BY ?title ?year ?rating
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "genres"])

    def search_by_genres(self, genres: list[str], limit: int = 6) -> list[dict]:
        """Αναζήτηση με πολλαπλά genres (OR λογική) — π.χ. Family + Animation."""
        filters = " || ".join(
            f'LCASE(STR(?filterGenre)) = "{g.lower()}"' for g in genres
        )
        q = f"""
        PREFIX ex: <{NS}>
        SELECT DISTINCT ?title ?year ?rating (GROUP_CONCAT(?g; separator=", ") AS ?genres)
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasGenre ?g .
            ?movie ex:hasGenre ?filterGenre .
            FILTER({filters})
        }}
        GROUP BY ?title ?year ?rating
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "genres"])

    def search_by_actor(self, name: str, limit: int = 5) -> list[dict]:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?title ?year ?rating WHERE {{
            ?actor a ex:Actor ;
                   ex:personName ?n ;
                   ex:hasPlayed ?movie .
            ?movie ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating .
            FILTER(CONTAINS(LCASE(STR(?n)), "{name.lower()}"))
        }}
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating"])

    def search_by_director(self, name: str, limit: int = 5) -> list[dict]:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?title ?year ?rating WHERE {{
            ?director a ex:Director ;
                      ex:personName ?n ;
                      ex:hasDirected ?movie .
            ?movie ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating .
            FILTER(CONTAINS(LCASE(STR(?n)), "{name.lower()}"))
        }}
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating"])

    def search_by_theme(self, keyword: str, limit: int = 5) -> list[dict]:
        """Αναζήτηση βάσει theme label — με GROUP BY για να μην εμφανίζεται η ίδια ταινία πολλές φορές."""
        q = f"""
        PREFIX ex: <{NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?title ?year ?rating (GROUP_CONCAT(?themeLabel; separator=", ") AS ?themes)
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasTheme ?theme .
            ?theme rdfs:label ?themeLabel .
            FILTER(CONTAINS(LCASE(STR(?themeLabel)), "{keyword.lower()}"))
        }}
        GROUP BY ?title ?year ?rating
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "themes"])

    def search_by_keyword(self, keyword: str, limit: int = 5) -> list[dict]:
        """Αναζήτηση βάσει keywords στο description field (tag cloud)."""
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?title ?year ?rating (GROUP_CONCAT(?genre; separator=", ") AS ?genres) ?description
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasGenre ?genre ;
                   ex:description ?description .
            FILTER(CONTAINS(LCASE(STR(?description)), "{keyword.lower()}"))
        }}
        GROUP BY ?title ?year ?rating ?description
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "genres", "description"])

    def search_by_keywords(self, keywords: list[str], limit: int = 6) -> list[dict]:
        """Αναζήτηση με πολλαπλά keywords (OR λογική) στο description field."""
        filters = " || ".join(
            f'CONTAINS(LCASE(STR(?description)), "{kw.lower()}")' for kw in keywords
        )
        q = f"""
        PREFIX ex: <{NS}>
        SELECT DISTINCT ?title ?year ?rating (GROUP_CONCAT(?genre; separator=", ") AS ?genres) ?description
        WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating ;
                   ex:hasGenre ?genre ;
                   ex:description ?description .
            FILTER({filters})
        }}
        GROUP BY ?title ?year ?rating ?description
        ORDER BY DESC(?rating)
        LIMIT {limit}
        """
        return self._run(q, ["title", "year", "rating", "genres", "description"])

    def get_movie_details(self, title_keyword: str) -> dict | None:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT ?movie ?title ?year ?rating ?description WHERE {{
            ?movie a ex:Movie ;
                   ex:movieTitle ?title ;
                   ex:releaseYear ?year ;
                   ex:rating ?rating .
            OPTIONAL {{ ?movie ex:description ?description . }}
            FILTER(CONTAINS(LCASE(STR(?title)), "{title_keyword.lower()}"))
        }}
        LIMIT 1
        """
        rows = list(self.g.query(q))
        if not rows:
            return None

        movie_uri  = str(rows[0].movie)
        title      = str(rows[0].title)
        year       = str(rows[0].year)
        rating     = str(rows[0].rating)
        description = str(rows[0].description) if rows[0].description else ""

        actors = [str(r.name) for r in self.g.query(f"""
            PREFIX ex: <{NS}>
            SELECT ?name WHERE {{
                ?a a ex:Actor ; ex:personName ?name ; ex:hasPlayed <{movie_uri}> .
            }}""")]

        directors = [str(r.name) for r in self.g.query(f"""
            PREFIX ex: <{NS}>
            SELECT ?name WHERE {{
                ?d a ex:Director ; ex:personName ?name ; ex:hasDirected <{movie_uri}> .
            }}""")]

        genres = [str(r.genre) for r in self.g.query(f"""
            PREFIX ex: <{NS}>
            SELECT ?genre WHERE {{ <{movie_uri}> ex:hasGenre ?genre . }}""")]

        themes = [str(r.label) for r in self.g.query(f"""
            PREFIX ex: <{NS}>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label WHERE {{
                <{movie_uri}> ex:hasTheme ?theme . ?theme rdfs:label ?label .
            }}""")]

        return {
            "title": title, "year": year, "rating": rating,
            "genres": genres, "directors": directors,
            "actors": actors, "themes": themes,
            "description": description,
        }

    def list_all_genres(self) -> list[str]:
        q = f"""
        PREFIX ex: <{NS}>
        SELECT DISTINCT ?genre WHERE {{
            ?m a ex:Movie ; ex:hasGenre ?genre .
        }} ORDER BY ?genre
        """
        return [str(r.genre) for r in self.g.query(q)]

    def list_all_themes(self) -> list[str]:
        q = f"""
        PREFIX ex: <{NS}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?label WHERE {{
            ?t a ex:Theme ; rdfs:label ?label .
        }} ORDER BY ?label
        """
        return [str(r.label) for r in self.g.query(q)]

    def _run(self, query: str, fields: list[str]) -> list[dict]:
        results = []
        for row in self.g.query(query):
            d = {}
            for f in fields:
                val = getattr(row, f, None)
                d[f] = str(val) if val is not None else "N/A"
            results.append(d)
        return results