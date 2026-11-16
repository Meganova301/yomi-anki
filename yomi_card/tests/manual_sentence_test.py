from src.sentence_generator import SentenceGenerator


generator = SentenceGenerator()

result = generator.generate_example(
    "見逃す",
    "みのがす",
    "to overlook; to miss"
)

print(result["japanese"])
print(result["english"])