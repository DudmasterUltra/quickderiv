import sys
import game
from expressions import Expression

if len(sys.argv) > 1:
    y = Expression(parse=''.join(sys.argv[1:]))
    dy = y.differentiate()
    dy.collect_terms()
    print(str(dy))
else:
    game.install_dependencies()
    import pygame
    game.play()
    #game.play((1920, 1080), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
