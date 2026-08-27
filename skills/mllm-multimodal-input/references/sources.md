# Sources (verified 2026-08-27)

| Fact | Source |
|---|---|
| Gemini image tokens: 258 for ≤ 384 px, 768-px tiles, crop-unit formula | https://ai.google.dev/gemini-api/docs/image-understanding |
| Gemini bounding boxes `[ymin, xmin, ymax, xmax]` 0–1000; segmentation JSON | https://ai.google.dev/gemini-api/docs/image-understanding |
| Gemini video 1 fps, 258/66 tokens per frame, 32 audio tokens per second | https://ai.google.dev/gemini-api/docs/video-understanding |
| Gemini implicit caching minimums (2048 / 4096) | https://ai.google.dev/gemini-api/docs/caching |
| Claude 28-px patches, resolution tiers (1568/1568 and 2576/4784), padding, limits | https://platform.claude.com/docs/en/build-with-claude/vision |
| Claude prefers absolute pixel coordinates; resize reference implementation | https://platform.claude.com/docs/en/build-with-claude/vision-coordinates |
| Claude prompt-cache minimums per model | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| OpenAI tile/patch image token rules and multipliers | https://developers.openai.com/api/docs/guides/images-vision |
| OpenAI prompt caching minimum 1024 (GPT-5.6+) / 2048, 30-minute retention | https://developers.openai.com/api/docs/guides/prompt-caching |
| Qwen2.5-VL 14-px patches, 2×2 merge, `min_pixels`/`max_pixels`, video `fps`/`num_frames` | https://github.com/QwenLM/Qwen2.5-VL |
| Qwen3-VL 16-px patches, 2×2 merge (32-px units), video `fps` 2 | https://github.com/QwenLM/Qwen3-VL (README; `qwen-vl-utils/src/qwen_vl_utils/vision_process.py` for the runtime constants) |
