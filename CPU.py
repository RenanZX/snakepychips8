import pygame
import random
import numpy as np
import os

fontset = [
  0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
  0x20, 0x60, 0x20, 0x20, 0x70, # 1
  0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
  0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
  0x90, 0x90, 0xF0, 0x10, 0x10, # 4
  0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
  0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
  0xF0, 0x10, 0x20, 0x40, 0x40, # 7
  0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
  0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
  0xF0, 0x90, 0xF0, 0x90, 0x90, # A
  0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
  0xF0, 0x80, 0x80, 0x80, 0xF0, # C
  0xE0, 0x90, 0x90, 0x90, 0xE0, # D
  0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
  0xF0, 0x80, 0xF0, 0x80, 0x80 #F
]

KeyMap = {
  pygame.K_1: 0x1,
  pygame.K_2: 0x2,
  pygame.K_3: 0x3,
  pygame.K_4: 0xC,

  pygame.K_q: 0x4,
  pygame.K_w: 0x5,
  pygame.K_e: 0x6,
  pygame.K_r: 0xD,

  pygame.K_a: 0x7,
  pygame.K_s: 0x8,
  pygame.K_d: 0x9,
  pygame.K_f: 0xE,

  pygame.K_z: 0xA,
  pygame.K_x: 0x0,
  pygame.K_c: 0xB,
  pygame.K_v: 0xF
}

# CPU do emulador Chip8
class CPU:
  opcode = 0x00
  memory = np.arange(4096,dtype=np.ubyte)
  V = np.arange(16,dtype=np.ubyte)
  I = 0
  pc = 0
  gfx = np.arange(2048,dtype=np.ubyte) #(64x32 screen)
  delay_timer = 0
  sound_timer = 0
  stack = np.arange(16,dtype=np.ushort)
  sp = 0
  key = [None] * 16

  def initCPU(self):
    self.pc = 0x200 # pc comeca em 0x200
    self.opcode = 0 # reset opcode atual
    self.I = 0 # reset index register
    self.sp = 0 # reset stack pointer
    # Clear display
    for i in range(2048):
      self.gfx[i] = 0
    # Clear stack
    for i in range(16):
      self.stack[i] = 0
      self.key[i] = False
      self.V[i] = 0 # Clear Registers V0-VF
    # Clear Memory
    for i in range(4096):
      self.memory[i] = 0
    # load fontset
    for i in range(80):
      self.memory[i] = fontset[i]
    
    # Clear Timers
    self.delay_timer = 0
    self.sound_timer = 0

    #Draw flag
    self.drawflag = True

    pass

  def Instr0x0000(self): #Set of instructions 0x00
    decode = self.opcode & 0x000F
    if decode == 0x0000: # 0x00E0: Clears the screen
      # Execute Opcode
      for i in range(2048):
        self.gfx[i] = 0
      
      self.drawflag = True
      self.pc += 2
    elif decode == 0x000E: # 0x00EE: Returns from subroutine
      self.sp-=1 # 16 levels of stack, decrease stack pointer to prevent overwrite
      self.pc = self.stack[self.sp]
      
      self.pc += 2
      # Execute Opcode
    else:
      print('Unknown opcode [0x0000]: ', hex(self.opcode), '\n')
    return

  def Instr0x1000(self): #1NNN: jumps to address NNN
    self.pc = self.opcode & 0x0FFF # eliminates first nible(1) to get address NNN
    return

  def Instr0x2000(self): #2NNN: calls a subrountine at NNN
    self.stack[self.sp] = self.pc
    self.sp+=1
    self.pc = self.opcode & 0x0FFF
    return

  def Instr0x3000(self): #3XNN: skips the next instruction if VX == NN
    if self.V[(self.opcode & 0x0F00) >> 8] == (self.opcode & 0x00FF):
      self.pc += 4
    else:
      self.pc += 2
    return

  def Instr0x4000(self): #4XNN: skips the next instruction if VX != NN
    if self.V[(self.opcode & 0x0F00) >> 8] != (self.opcode & 0x00FF):
      self.pc += 4
    else:
      self.pc += 2
    return

  def Instr0x5000(self): #5XY0: skips the next instruction if VX == VY
    if self.V[(self.opcode & 0x0F00) >> 8] == self.V[(self.opcode & 0x00F0) >> 4]:
      self.pc += 4
    else:
      self.pc += 2
    return

  def Instr0x6000(self): #6XNN: Sets VX to NN
    self.V[(self.opcode & 0x0F00) >> 8] = self.opcode & 0x00FF
    self.pc += 2
    return

  def Instr0x7000(self): #7XNN: Adds NN to VX(Carry flag is not changed)
    self.V[(self.opcode & 0x0F00) >> 8] += self.opcode & 0x00FF
    self.pc += 2
    return

  def Instr0x8000(self): #8XYN: Sets of Instructions 0x8
    decode = {
      0x0000:self.Instr0x8XY0,
      0x0001:self.Instr0x8XY1,
      0x0002:self.Instr0x8XY2,
      0x0003:self.Instr0x8XY3,
      0x0004:self.Instr0x8XY4,
      0x0005:self.Instr0x8XY5,
      0x0006:self.Instr0x8XY6,
      0x0007:self.Instr0x8XY7,
      0x000E:self.Instr0x8XYE
    }

    if (self.opcode & 0x000F) in decode:
      decode[self.opcode & 0x000F]()
    else:
      print('Unknown opcode [0x8000]: ', hex(self.opcode), '\n')
    return

  def Instr0x8XY0(self): #8XY0: Sets VX to value of VY (VX = VY)
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass
  
  def Instr0x8XY1(self): #8XY1: Sets VX to VX or VY (VX = VX or VY)
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x0F00) >> 8] | self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass

  def Instr0x8XY2(self): #8XY2: Sets VX to VX and VY (VX = VX and VY)
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x0F00) >> 8] & self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass
  
  def Instr0x8XY3(self): #8XY3: Sets VX to VX xor VY (VX = VX xor VY)
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x0F00) >> 8] ^ self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass

  def Instr0x8XY4(self): #8XY4: Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't.(VX += VY)
    if self.V[(self.opcode & 0x00F0) >> 4] > (0xFF - self.V[(self.opcode & 0x0F00) >> 8]): #if VY > 0xFF - VX
      self.V[0xF] = 1 #Carry
    else:
      self.V[0xF] = 0

    self.V[(self.opcode & 0x0F00) >> 8] += self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass
  
  def Instr0x8XY5(self): #8XY5:VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't. (VX -= VY)
    if self.V[(self.opcode & 0x00F0) >> 4] > self.V[(self.opcode & 0x0F00) >> 8]:
      self.V[0xF] = 0 #Borrow
    else:
      self.V[0xF] = 1

    self.V[(self.opcode & 0x0F00) >> 8] -= self.V[(self.opcode & 0x00F0) >> 4]
    self.pc += 2
    pass
    
  def Instr0x8XY6(self): #8XY6:Stores the least significant bit of VX in VF and then shifts VX to the right by 1.(VX >>= 1)
    self.V[0xF] = self.V[(self.opcode & 0x0F00) >> 8] & 0x1
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x0F00) >> 8] >> 1
    self.pc += 2
    pass
    
  def Instr0x8XY7(self): #8XY7:Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't.(VX=VY-VX)
    if self.V[(self.opcode & 0x0F00) >> 8] > self.V[(self.opcode & 0x00F0) >> 4]:
      self.V[0xF] = 0 #Borrow
    else:
      self.V[0xF] = 1
          
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x00F0) >> 4] - self.V[(self.opcode & 0x0F00) >> 8]
    self.pc += 2
    pass

  def Instr0x8XYE(self): #8XYE:Stores the most significant bit of VX in VF and then shifts VX to the left by 1.(VX << 1)
    self.V[0xF] = self.V[(self.opcode & 0x0F00) >> 8] >> 7
    self.V[(self.opcode & 0x0F00) >> 8] = self.V[(self.opcode & 0x0F00) >> 8] << 1
    self.pc += 2
    pass

  def Instr0x9000(self): # 9XY0: Skips the next instruction if VX doesn't equal VY. (Usually the next instruction is a jump to skip a code block)(if VX!=VY)
    if self.V[(self.opcode & 0x0F00) >> 8] != self.V[(self.opcode & 0x00F0) >> 4]:
      self.pc += 4
    else:
      self.pc+=2
    return

  def Instr0xA000(self): #ANNN: Sets I to the address NNN
    #Execute code
    self.I = self.opcode & 0x0FFF
    self.pc += 2
    return

  def Instr0xB000(self): #BNNN: Jumps to the address NNN plus V0.
    self.pc = self.opcode & 0x0FFF + self.V[0x0]
    return

  def Instr0xC000(self): #CXNN: Sets VX to the result of a bitwise and operation on a random number (Typically: 0 to 255) and NN.
    self.V[(self.opcode & 0x0F00) >> 8] = random.randint(0,255) & (self.opcode & 0x00FF)
    self.pc += 2
    return
  
  def Instr0xD000(self): #DXYN: Draws a sprite at coordinate (VX, VY) 
                             #that has a width of 8 pixels and a height of N pixels.
                             # Each row of 8 pixels is read as bit-coded starting from memory location I; 
                             # I value doesn’t change after the execution of this instruction. 
                             # As described above, VF is set to 1 if any screen pixels are flipped 
                             # from set to unset when the sprite is drawn, and to 0 if that doesn’t happen
    x = self.V[(self.opcode & 0x0F00) >> 8]
    y = self.V[(self.opcode & 0x00F0) >> 4]
    height = self.opcode & 0x000F
    self.V[0xF] = 0

    for yline in range(height):
      ind = self.I + yline
      pixel = self.memory[ind]
      #print('pixel value:',pixel)
      for xline in range(8):
        if (pixel & (0x80 >> xline)) != 0:
          #print('x:',x,' xline:',xline,' y:',y,' yline:',yline,'gfxpos=',(x + xline + ((y + yline) * 64)),'\n')
          pos = x + xline + ((y + yline) * 64)
          if pos >= 2048:
            pos = 2047
          elif pos < 0:
            pos = 0

          if self.gfx[pos] == 1:
            self.V[0xF] = 1
          self.gfx[pos] ^=1


    self.drawflag = True
    self.pc+=2
    return

  def Instr0xE000(self): # Test key Input
    decode = self.opcode & 0x00FF
    if decode == 0x009E: #if(Key() == Vx)
      if self.key[self.V[(self.opcode & 0x0F00) >> 8]] == True:
        self.pc += 4
      else:
        self.pc += 2
    elif decode == 0x00A1: #if(Key() != Vx)
      if self.key[self.V[(self.opcode & 0x0F00) >> 8]] != True:
        self.pc += 4
      else:
        self.pc += 2
    return

  def Instr0xF000(self):
    decode = {
      0x0007:self.Instr0xFX07,
      0x000A:self.Instr0xFX0A,
      0x0015:self.Instr0xFX15,
      0x0018:self.Instr0xFX18,
      0x001E:self.Instr0xFX1E,
      0x0029:self.Instr0xFX29,
      0x0033:self.Instr0xFX33,
      0x0055:self.Instr0xFX55,
      0x0065:self.Instr0xFX65
    }

    if (self.opcode & 0x00FF) in decode:
      decode[self.opcode & 0x00FF]()
    else:
      print('Unknown opcode: 0xF000', hex(self.opcode), '\n')
    return
  
  def Instr0xFX07(self): # 0xFX07: Sets VX to the value of the delay timer.(Vx = get_delay())
    self.V[(self.opcode & 0x0F00) >> 8] = self.delay_timer
    self.pc+=2
    pass
    
  def Instr0xFX0A(self): # 0xFX0A: A key press is awaited, and then stored in VX. (Blocking Operation. All instruction halted until next key event)(Vx = get_key())
    keypress = False
    for i in range(16):
      if self.key[i] != False:
        self.V[(self.opcode & 0x0F00) >> 8] = i
        keypress = True
          
    if not keypress: #if didn't receive a keypress, skip this cycle and try again
      return
    self.pc+=2
    pass
    
  def Instr0xFX15(self): # 0xFX15: Sets the delay timer to VX. (delay_timer(Vx))
    self.delay_timer = self.V[(self.opcode & 0x0F00) >> 8]
    self.pc+=2
    pass
    
  def Instr0xFX18(self): # 0xFX18: Sets the sound timer to VX. (sound_timer(Vx))
    self.sound_timer = self.V[(self.opcode & 0x0F00) >> 8]
    self.pc+=2
    pass
    
  def Instr0xFX1E(self): # 0xFX1E: Adds VX to I. VF is not affected (I+=Vx)
    if (self.I + self.V[(self.opcode & 0x0F00) >> 8]) > 0xFFF: # VF is set to 1 when overflow I+V[x] > 0xFFF
      self.V[0xF] = 1
    else:
      self.V[0xF] = 0
      
    self.I += self.V[(self.opcode & 0x0F00) >> 8]
    self.pc+=2
    pass
    
  def Instr0xFX29(self): # 0xFX29: Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.
    self.I = self.V[(self.opcode & 0x0F00) >> 8] * 0x5
      
    self.pc+=2
    pass
    
  def Instr0xFX33(self): # 0xFX33 BCD
    self.memory[self.I] = self.V[(self.opcode & 0x0F00) >> 8] / 100
    self.memory[self.I + 1] = (self.V[(self.opcode & 0x0F00) >> 8] / 10) % 10
    self.memory[self.I + 2] = (self.V[(self.opcode & 0x0F00) >> 8] % 100) % 10
      
    self.pc+=2
    pass
    
  def Instr0xFX55(self): # 0xFX55: Stores V0 to VX (including VX) in memory starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified.
    for i in range((self.opcode & 0x0F00) >> 8):
      self.memory[self.I + i] = self.V[i]
          
    self.I+= ((self.opcode & 0x0F00) >> 8) + 1
    self.pc+=2
    pass

  def Instr0xFX65(self): # 0xFX65: Fills V0 to VX (including VX) with values from memory starting at address I. The offset from I is increased by 1 for each value written, but I itself is left unmodified
    for i in range((self.opcode & 0x0F00) >> 8):
      self.V[i] = self.memory[self.I + i]
          
    self.I+= ((self.opcode & 0x0F00) >> 8) + 1
    self.pc+=2
    pass

  def EmulateCycle(self):
    # Fetch code
    self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    #Decode code
    decode = {
      0x0000: self.Instr0x0000,
      0x1000: self.Instr0x1000,
      0x2000: self.Instr0x2000,
      0x3000: self.Instr0x3000,
      0x4000: self.Instr0x4000,
      0x5000: self.Instr0x5000,
      0x6000: self.Instr0x6000,
      0x7000: self.Instr0x7000,
      0x8000: self.Instr0x8000,
      0x9000: self.Instr0x9000,
      0xA000: self.Instr0xA000,
      0xB000: self.Instr0xB000,
      0xC000: self.Instr0xC000,
      0xD000: self.Instr0xD000,
      0xE000: self.Instr0xE000,
      0xF000: self.Instr0xF000
    }

    if (self.opcode & 0xF000) in decode:
      decode[(self.opcode & 0xF000)]()
    else:
      print('Unknown opcode: ', hex(self.opcode), '\n')
    
    #Update timers
    if self.delay_timer > 0:
      self.delay_timer-=1

    if self.sound_timer > 0:
      if self.sound_timer == 1:
        print('BEEP!\n')

      self.sound_timer-=1
    pass

  def loadGame(self,game):
      self.initCPU()
      print("Carregando Rom...\n")

      f = open(game,'rb')

      if not f:
        print('Arquivo ou diretório não existe!\n')
      
      f.seek(0,os.SEEK_END)
      sizefile = f.tell()
      print("Tamanho do arquivo: ",sizefile,'\n')

      f.seek(0)

      if (4096-512) > sizefile:
        byte = f.read(1)
        i = 0
        while byte:
          self.memory[i+512] = int.from_bytes(byte, byteorder='big')
          byte = f.read(1)
          i+=1
      else:
        print("Erro ROM é muito grande para ser carregada na memória\n")

      f.close()
      pass

  def setKeyDown(self,value):
    if value in KeyMap:
      self.key[KeyMap[value]] = True
    pass

  def setKeyUp(self,value):
    if value in KeyMap:
      self.key[KeyMap[value]] = False
    pass


#Tela para mostrar o emulador rodando
class Screen:
  width = 64
  height = 32
  scale = 20
  ps = 30 #pixel size
  
  def __init__(self):
    pygame.init()
    pygame.display.set_caption('SnakePyChips8 - Chip8 Emulator')
    self.win = pygame.display.set_mode((self.width*self.scale,self.height*self.scale))

  def render(self,gfx):
    for i in range(self.height):
      for j in range(self.width):
        if gfx[i*self.width + j] == 1:
          color = (255,255,255)
        else:
          color = (0,0,0)

        pygame.draw.rect(self.win,color,(j*self.scale,i*self.scale,self.ps,self.ps),0)


  def closeWin(self):
    pygame.quit()
  