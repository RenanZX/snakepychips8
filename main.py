from CPU import *
import sys

# seta o sistema de renderização
g = Screen()

# Inicializa o Sistema Chip8 e carrega o jogo na memória
cpu = CPU()
cpu.loadGame(sys.argv[1])

running = True
#Emulation Loop
while(running):
    # Emular um ciclo
    cpu.EmulateCycle()

    # Se a flag de desenho esta ativa, atualiza a tela   
    if cpu.drawflag:
        g.render(cpu.gfx)

    # Armazena o estado da tecla pressionada(pressionar e soltar)
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            cpu.setKeyDown(event.key)
    
        if event.type == pygame.KEYUP:
            cpu.setKeyUp(event.key)
    
    pygame.display.flip()

g.closeWin()