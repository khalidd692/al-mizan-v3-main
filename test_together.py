from together import Together

client = Together(api_key="tgp_v1_nOvoLrtzoVy_76t5Md2sx-n3BENVHLejoz8hyAgq610")  # clé API insérée temporairement

response = client.chat.completions.create(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    messages=[
      {
        "role": "user",
        "content": "What are some fun things to do in New York?"
      }
    ]
)
print(response.choices[0].message.content)