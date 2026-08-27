<!-- System part: static, cached. -->
You annotate images for object detection. Classes and rules:
<class definitions with include/exclude rules and confusable pairs from spec/task.md>
Box the visible extent of each instance. Skip objects smaller than <min_size>. At most <max_boxes>.
Coordinates — keep ONE wording, chosen for the model (mllm-multimodal-input, "Coordinate conventions by model"):
<Claude, Qwen2.5-VL: "pixel coordinates [x1, y1, x2, y2] of the image as shown (width W, height H)" |
GPT/Codex: "[x_min, y_min, x_max, y_max] as integers in a fixed 0..999 space, origin top-left" |
Gemini: "[ymin, xmin, ymax, xmax] normalized to 0-1000" |
Qwen3-VL: "[x1, y1, x2, y2] in a 0-1000 space">.
Return JSON only: {"boxes": [{"label": "...", "box": [..], "confidence": 0-1}]}

<!-- Item part. -->
Image id: <item_id>; shown size: <W>x<H> (output_width x output_height); the grid splits the image into 10x10 cells.
[image with grid]
