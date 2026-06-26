from openai import OpenAI

SYSTEM_PROMPT = """You are a friendly movie recommendation assistant.
You have access ONLY to a specific movie ontology.

RULES:
1. Recommend ONLY movies provided to you as data — suggesting others is FORBIDDEN.
2. ALWAYS use the English titles as given (e.g. "The Dark Knight", "Inception").
3. If no results are found, say that no movies matched the criteria.
4. ALWAYS reply in English, regardless of what language the user writes in.
5. Keep answers concise (2-3 lines max per movie).
6. Do NOT use markdown (**, ##) — plain text only for Telegram."""


class OpenAILLM:
    def __init__(self, api_key: str, model: str = "meta/llama-3.1-8b-instruct"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.model = model

    def _chat(self, user_content: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_content},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ Error: {e}"

    def recommend(self, movies: list[dict], user_query: str) -> str:
        if not movies:
            context = "No movies found in the ontology matching these criteria."
        else:
            lines = []
            for m in movies:
                parts = [f"Title: {m.get('title', '?')}",
                         f"Year: {m.get('year', '?')}",
                         f"Rating: {m.get('rating', '?')}"]
                if m.get("genres") and m["genres"] != "N/A":
                    parts.append(f"Genres: {m['genres']}")
                if m.get("themes") and m["themes"] != "N/A":
                    parts.append(f"Themes: {m['themes']}")
                if m.get("description") and m["description"] != "N/A":
                    parts.append(f"Keywords: {m['description']}")
                lines.append(" | ".join(parts))
            context = "Movies from the ontology:\n" + "\n".join(f"- {l}" for l in lines)

        prompt = f"""The user requested: "{user_query}"

{context}

Recommend ONLY the movies listed above using their English titles.
Explain why they match what the user asked for, using the keywords and themes as context."""
        return self._chat(prompt)

    def describe_movie(self, details: dict) -> str:
        actors      = ", ".join(details.get("actors", [])) or "Unknown"
        directors   = ", ".join(details.get("directors", [])) or "Unknown"
        genres      = ", ".join(details.get("genres", [])) or "N/A"
        themes      = ", ".join(details.get("themes", [])) or "N/A"
        description = details.get("description", "") or "N/A"

        prompt = f"""The user asked about the movie "{details['title']}".

Information from the ontology:
- Title: {details['title']}
- Year: {details['year']}
- Rating: {details['rating']}
- Genres: {genres}
- Director: {directors}
- Actors: {actors}
- Themes: {themes}
- Keywords: {description}

Write a short, engaging description using the English title "{details['title']}".
Use the keywords and themes to make the description more accurate and vivid."""
        return self._chat(prompt)

    def free_chat(self, user_message: str) -> str:
        prompt = f"""The user wrote: "{user_message}"

No matching movies were found in the ontology.
Do NOT suggest movies from your own knowledge.
Politely say no results were found and suggest they search by:
genre (e.g. Action, Drama), actor, director, theme, or keyword (e.g. space, love, war)."""
        return self._chat(prompt)