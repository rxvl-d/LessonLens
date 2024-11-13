from pathlib import Path
import os

print(Path(os.getenv('HOME')) / '.cache' / 'LessonLens')
