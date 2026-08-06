from pptx import Presentation
prs = Presentation()
for i, layout in enumerate(prs.slide_layouts):
    print(f'layout {i}: {layout.name}')
    for shape in layout.shapes:
        pf = getattr(shape, 'placeholder_format', None)
        if pf is not None:
            print(f'  shape id={shape.shape_id}, name={shape.name}, type={shape.shape_type}, placeholder idx={pf.idx}, type={pf.type}')
        else:
            print(f'  shape id={shape.shape_id}, name={shape.name}, type={shape.shape_type}, placeholder=None')
