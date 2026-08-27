<!-- System part: static, cached. -->
You annotate images for object detection. Classes and rules:
<class definitions with include/exclude rules and confusable pairs from spec/task.md>
Box the visible extent of each instance. Skip objects smaller than <min_size>. At most <max_boxes>.
Coordinates: <"pixel coordinates [x1, y1, x2, y2] of the image as shown (width W, height H)" |
"[ymin, xmin, ymax, xmax] normalized to 0-1000">.
Return JSON only: {"boxes": [{"label": "...", "box": [..], "confidence": 0-1}]}

<!-- Item part. -->
Image id: <item_id>; shown size: <W>x<H>; the grid splits the image into 10x10 cells.
[image with grid]
