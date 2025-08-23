from author_filter import rate_profile
score, reason = rate_profile("https://x.com/funkiidotsui", env_path=".env")
print(f"Score: {score}/10, Reason: {reason}")
