import tkinter as tk
import math
import decrypt,process_encryption, random, pycipher, numpy as np
from analyse import quadgram_score, chisqr, indice_coincidence
import pycipher
from itertools import permutations
from tkinter import ttk
from tkinter import messagebox
from graphing import *
from analyse import *
import re
fitness = quadgram_score()
LARGE_FONT = ("Verdana", 12)

# Container and page handling - Do not touch
class Crypt(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.option_add("*Font", "Helvetica 11")
        self.geometry('{}x{}'.format(700, 680))
        self.title("Cryptanalysis Toolbox v2.0 by Dulhan Jayalath")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (main_page, PageOne):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(main_page)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# Main page on open
modified = False
class main_page(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # Ciphertext input box
        ttk.Label(self,text="Encrypted Text").grid(row=0,column=1,columnspan=10,pady=5)
        scrollbar = ttk.Scrollbar(self)
        scrollbar.grid(row=1,column=2,sticky=tk.NSEW)

        cipher_input = tk.Text(self, wrap=tk.WORD, yscrollcommand=scrollbar.set,height=5,width=80)
        cipher_input.grid(row=1,column=1,padx=(20,0))

        scrollbar.config(command=cipher_input.yview)

        def get_cipher():
            return re.sub('[^A-Za-z0-9]+', '', cipher_input.get('1.0', tk.END)).upper()

        # Text manipulation options
        def save_text():
            global text_orig
            text_orig = cipher_input.get('1.0', tk.END)
            global modified
        def reverse_word_lettering():
            #re.sub(r'([^\s\w]|_)+', '', origList)
            global modified
            if modified == False:
                save_text()
            text = cipher_input.get('1.0',tk.END).replace('\n','').replace('\r','').split(' ')
            reversed_text = []
            for word in text:
                reversed_text.append(word[::-1])
            cipher_input.delete('1.0',tk.END)
            reversed_text = " ".join(reversed_text)
            cipher_input.insert(tk.INSERT, reversed_text)
            modified = True
        def reverse_string():
            global modified
            if modified == False:
                save_text()
            text = cipher_input.get('1.0', tk.END).replace('\n', '').replace('\r', '')
            cipher_input.delete('1.0', tk.END)
            cipher_input.insert(tk.INSERT, text[::-1])
            modified = True
        def reset_string():
            global text_orig
            cipher_input.delete('1.0', tk.END)
            cipher_input.insert(tk.INSERT, text_orig)
        def clear():
            global text_orig
            text_orig = ""
            global modified
            modified = False
            cipher_input.delete('1.0', tk.END)

        # Text Manipulation Buttons
        manipulation_frame = ttk.Frame(self)
        ttk.Button(manipulation_frame,text="Reverse Full String",command=lambda: reverse_string()).grid(row=0,column=0)
        ttk.Button(manipulation_frame,text="Reverse Word Lettering",command=lambda: reverse_word_lettering()).grid(row=0,column=1,padx=2)
        ttk.Button(manipulation_frame,text="Reset Full String",command=lambda: reset_string()).grid(row=0,column=2,padx=(0,2))
        ttk.Button(manipulation_frame,text="Clear",command=lambda: clear()).grid(row=0,column=3,padx=(0,2))
        manipulation_frame.grid(row=2,column=1,sticky=tk.W,padx=(20,0),pady=5)


        # Frame enclosing statistics, graphs and decryption labelframes
        layer_frames = ttk.Frame(self)
        # Statistics Frame
        stats = ttk.LabelFrame(layer_frames,text="Statistics",width=200)

        ttk.Label(stats,text="Index of Coincidence",font="Helvetica 8").grid(row=0,column=0,sticky=tk.W)#
        ic = ttk.Label(stats,text="0.0000",font="Helvetica 8 bold")
        ic.grid(row=0,column=2,sticky=tk.E)

        ttk.Label(stats,text="Characters",font="Helvetica 8").grid(row=1,column=0,sticky=tk.W)
        charcount = ttk.Label(stats,text="0",font="Helvetica 8 bold")
        charcount.grid(row=1,column=2,sticky=tk.E)

        ttk.Label(stats,text="Key-length (Confidence)",font="Helvetica 8").grid(row=2,column=0,sticky=tk.W)
        periodic = ttk.Label(stats,text="0",font="Helvetica 8 bold")
        periodic.grid(row=2,column=1,sticky=tk.E)

        difference = ttk.Label(stats,text="(0.00%)",font="Helvetica 8 bold")
        difference.grid(row=2,column=2,sticky=tk.W)

        stats.grid(row=0,column=0,sticky=tk.NSEW,padx=(20,0),pady=5)
        stats.grid_propagate(False)



        # Live updating calculations
        def typing(event):

            text = re.sub('[^A-Za-z0-9]+', '', cipher_input.get('1.0', tk.END)).upper()

            char_count = len(text)
            char_string = str(char_count)
            charcount.config(text=char_string)

            ic_score = round(indice_coincidence(text),4)
            if len(str(ic_score)) != 6:
                ic_score = str(ic_score)
                while len(ic_score) != 6:
                    ic_score += "0"
            displayed_string = str(ic_score)
            ic.config(text = displayed_string)

            periodic_calc = period_ic()
            highest_ic_fig = periodic_calc.index(max(periodic_calc)) + 2
            highest_ic = max(periodic_calc)
            periodic_calc.remove(max(periodic_calc))
            next_ic = max(periodic_calc)
            diff = round(((highest_ic - next_ic)/next_ic)*100,2)
            periodic.config(text=str(highest_ic_fig))
            difference.config(text="(" + str(diff) + "%)")

        cipher_input.bind('<KeyRelease>',typing)

        # Periodic IC calculations
        def period_ic():
            xtext = get_cipher()
            average = []
            for j in range(2, 21):
                sequence = []
                for k in range(j):
                    text = list(xtext[k:])
                    n = j
                    output = []
                    i = 0
                    while i < len(text):
                        output.append(text[i])
                        i = i + int(n)
                    phrase = "".join(output)
                    sequence.append(indice_coincidence(phrase))  # Calculate each index of coincidence
                average.append(sum(sequence) / len(sequence))
            return average

        # Graphs frame
        graphs = ttk.LabelFrame(layer_frames,text="Graphs")

        ttk.Button(graphs,text="Periodic IC",command=lambda: icgraph(get_cipher()),width=20).grid(row=0,column=0,sticky=tk.W)
        ttk.Button(graphs,text="Monogram Frequency",command=lambda: freqanalysis(get_cipher()),width=20).grid(row=1,column=0,pady=5,sticky=tk.W)

        graphs.grid(row=0,column=1,sticky=tk.NSEW,padx=10,pady=5)

        layer_frames.grid(row=3,column=1,columnspan=10,sticky=tk.EW)

        #Decrypted Text output
        ttk.Label(self,text="Decrypted Text").grid(row=4,column=1,columnspan=10,pady=5)
        scrollbar2 = ttk.Scrollbar(self)
        scrollbar2.grid(row=5,column=2,sticky=tk.NSEW)

        cipher_output = tk.Text(self, wrap=tk.WORD, yscrollcommand=scrollbar2.set,height=5,width=80)
        cipher_output.grid(row=5,column=1,padx=(20,0))

        scrollbar2.config(command=cipher_output.yview)
        pbprogress = tk.IntVar(self)
        pb = ttk.Progressbar(self, orient="horizontal",length=644, variable=pbprogress, mode="determinate")
        pb.grid(row=6,column=1,pady=5,padx=(20,0),sticky=tk.W)

        # Statistics after decryption
        final_layer = tk.Frame(self)

        decryptionstats = ttk.LabelFrame(final_layer,text="Results",width=134)
        decryptionstats.grid(row=0,column=3,sticky=tk.NSEW,padx=5)
        decryptionstats.grid_propagate(False)
        ttk.Label(decryptionstats,text="Keys Tested",font="Helvetica 9 bold",anchor=tk.CENTER).grid(row=0,column=0,sticky="ew",padx=5,pady=(2.5,0))
        keystested = ttk.Label(decryptionstats,text="0",font="Helvetica 12",anchor=tk.CENTER)
        keystested.grid(row=1,column=0,sticky="ew",padx=5,pady=5)
        ttk.Label(decryptionstats,text="Best Fitness",font="Helvetica 9 bold",anchor=tk.CENTER).grid(row=2,column=0,sticky="ew",padx=5,pady=(2.5,0))
        bestfitness = ttk.Label(decryptionstats,text="0",font="Helvetica 12",anchor=tk.CENTER)
        bestfitness.grid(row=3,column=0,sticky="ew",padx=5,pady=5)
        ttk.Label(decryptionstats,text="Best Key",font="Helvetica 9 bold",anchor=tk.CENTER).grid(row=4,column=0,sticky="ew",padx=5,pady=(2.5,0))
        bestkey = ttk.Label(decryptionstats,text="-",font="Helvetica 9",anchor=tk.CENTER)
        bestkey.grid(row=5,column=0,sticky="ew",padx=5,pady=5)

        top_keys = ttk.LabelFrame(final_layer,text="Top Keys",height=250,width=180)
        keys_top = {}
        for i in range(10):
            ttk.Label(top_keys,text=str(i+1) + ".").grid(row=i,column=0)
            keys_top[i] = ttk.Label(top_keys,text="",font="Courier 10")
            keys_top[i].grid(row=i,column=1,sticky=tk.NW)

        top_keys.grid(row=0,column=0,sticky=tk.NW,padx=5)
        top_keys.grid_propagate(False)

        # Decryption options frame
        decryptionconfig = ttk.LabelFrame(final_layer,text="Decryption",width=300,height=50)
        decryptionconfig.grid(row=0,column=2,sticky=tk.NSEW,padx=5)
        decryptionconfig.grid_propagate(False)
        selected_cipher = tk.StringVar(decryptionconfig)
        ttk.Label(decryptionconfig,text="Cipher Type",font="Helvetica 9 bold").grid(row=1,column=0,sticky=tk.W,padx=5,pady=(5,0))
        cipher_list = ttk.OptionMenu(decryptionconfig, selected_cipher, "Vigenere", "Vigenere", "Beaufort", "Caesar","Polybius")
        cipher_list.grid(row=1,column=1,padx=5,sticky="ew")
        cipher_list.grid_propagate(False)

        def set_cipherselection(v,cipher_list):
            if v.get() == 1:
                cipher_list.grid_forget()
                # Edit this one for effect
                cipher_list = ttk.OptionMenu(decryptionconfig,selected_cipher,"Vigenere","Vigenere","Beaufort","Caesar","Substitution","Columnar","Polybius","Hill (2x2)","Hill (3x3)")
                cipher_list.grid(row=1, column=1, padx=5, sticky="ew")
                cipher_list.grid_propagate(False)
            else:
                cipher_list.grid_forget()
                cipher_list = ttk.OptionMenu(decryptionconfig,selected_cipher,"Vigenere/Affine","Vigenere/Affine","Vigenere/Scytale")
                cipher_list.grid(row=1, column=1, padx=5, sticky="ew")
                cipher_list.grid_propagate(False)

        v = tk.IntVar(decryptionconfig)
        ttk.Label(decryptionconfig,text="Cipher Layers",font="Helvetica 9 bold").grid(row=0,column=0,sticky=tk.W,padx=5)
        radio1 = ttk.Radiobutton(decryptionconfig,text="Single",command=lambda: set_cipherselection(v,cipher_list),variable=v,value=1,state="normal")
        radio1.grid(row=0,column=1,padx=(5,0),sticky=tk.W)
        radio1.invoke()
        ttk.Radiobutton(decryptionconfig, text="Double",command=lambda: set_cipherselection(v,cipher_list), variable=v, value=2).grid(row=0, column=1,sticky=tk.W,pady=5,padx=(70,0))



        selected_period = tk.StringVar(decryptionconfig)

        key = ttk.Entry(decryptionconfig,text="key")
        key.grid(row=2,column=1,padx=5,sticky="ew")
        ttk.Label(decryptionconfig,text="Key (Optional)",font="Helvetica 9 bold").grid(row=2,column=0,sticky=tk.W,padx=5,pady=10)



        ttk.Label(decryptionconfig,text="Period (Optional)",font="Helvetica 9 bold").grid(row=3,column=0,sticky=tk.W,padx=5)
        period_selection = ttk.OptionMenu(decryptionconfig,selected_period,"-","-","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15")
        period_selection.grid(row=3,column=1,sticky="ew",padx=5)

        #Solve Button
        stop = False
        ttk.Button(decryptionconfig,text="SOLVE",command=lambda: solve_cipher(selected_cipher.get(),pbprogress)).grid(row=4,column=0,columnspan=2,padx=5,pady=(10,0),sticky=tk.NSEW)
        stopper = ttk.Button(decryptionconfig, text="STOP",command=lambda: stop_cipher(pbprogress),state=tk.DISABLED)
        stopper.grid(row=5, column=0, columnspan=2,padx=5, pady=5,sticky=tk.NSEW)
        def stop_cipher(pbprogress):
            pb.stop()
            global stop
            stop = True
            pb.config(mode='determinate')
            pbprogress.set(0)
            pb.update()

        final_layer.grid(row=7,column=1,sticky=tk.NW,pady=5,padx=(20,0))

        def restore(text):
            text = list(text)
            for i in range(len(nonalphabetic)):
                text.insert(nonalphabetic[i][1], nonalphabetic[i][0])
            for i in range(len(case)):
                text[case[i]] = text[case[i]].lower()
            return "".join(text)

        def key_updater(top10keys):
            top10keys = top10keys[-10:]
            for i in range(10):
                keys_top[9 - i].config(text=top10keys[i])

        # Decryption button action
        def solve_cipher(cipher,pbprogress):
            for i in range(10):
                keys_top[i].config(text="")
            bestkey.config(text="-")
            bestfitness.config(text="0")
            keystested.config(text="0")
            pbprogress.set(0)
            pb.update()

            #Save non-alphabetic characters
            global nonalphabetic
            nonalphabetic = []
            raw_text = cipher_input.get('1.0',tk.END)
            alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
            global case
            case = []
            for i in range(len(raw_text)):
                if raw_text[i] not in alphabet:
                    nonalphabetic.append([raw_text[i],i])
                else:
                    if raw_text[i].islower() is True:
                        case.append(i)

            if cipher == "*Select Cipher":
                messagebox.showerror("Decryption","No cipher selected")
            elif cipher == "Vigenere":
                if key.get() == "":
                    crack_vigenere(get_cipher(),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.vigenere(process_encryption.process2(get_cipher()),key.get().upper())))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Beaufort":
                if key.get() == "":
                    crack_beaufort(get_cipher(),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.vigenere(decrypt.atbash(process_encryption.process2(get_cipher())),decrypt.atbash(key.get().upper()))))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Caesar":
                if key.get() == "":
                    crack_caesar(process_encryption.process2(get_cipher()),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.caesar(process_encryption.process2(get_cipher()),key.get().upper())))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Columnar":
                if key.get() == "":
                    crack_coltrans(process_encryption.process2(get_cipher()),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(pycipher.ColTrans(key.get().upper()).decipher(process_encryption.process2(get_cipher()))))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Polybius":
                if key.get() == "":
                    crack_polybius(process_encryption.process2(get_cipher()),pbprogress)
            elif cipher == "Hill (2x2)":
                if key.get() == "":
                    crack_2x2hill(get_cipher(),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.hill2x2(get_cipher(),key.get())))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Hill (3x3)":
                if key.get() == "":
                    crack_3x3hill(get_cipher(),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.hill3x3(get_cipher(),key.get())))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Substitution":
                if key.get() == "":
                    crack_substitution(get_cipher(),pbprogress)
                else:
                    alpha = list("ABCDEFGHIKLMNOPQRSTUVWXYZ")
                    key_in_use = key.get().upper()
                    if len(key_in_use) != 26:
                        for letter in key_in_use:
                            alpha.remove(letter)
                    key_in_use = key_in_use + "".join(alpha)
                    print(key_in_use)
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.substitution(get_cipher(),key_in_use)))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Vigenere/Affine":
                if key.get() == "" or selected_period.get() == "-":
                    crack_vigenere_affine(get_cipher(),pbprogress)
                else:
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(decrypt.vigenereaffine(get_cipher(),key.get().upper(),int(selected_period.get()))))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()
            elif cipher == "Vigenere/Scytale":
                if key.get() == "" and selected_period.get() == "-":
                    crack_vigenere_scytale(get_cipher(),pbprogress)
                elif selected_period.get() != "-":
                    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    crack_vigenere(pycipher.ColTrans(alphabet[0:int(selected_period.get())]).decipher(get_cipher()),pbprogress)
                elif key.get() != "":
                    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    bestsofar = -99e9
                    count = 0
                    for scytale in range(1, 11):
                        cipher2 = decrypt.vigenere(pycipher.ColTrans(alphabet[0:scytale + 1]).decipher(get_cipher()),key.get().upper())
                        print(cipher2)
                        chill = fitness.score(cipher2)
                        if chill > bestsofar:
                            bestsofar = chill
                            cipher_output.delete('1.0', tk.END)
                            cipher_output.insert(tk.INSERT, restore(cipher2))
                            cipher_output.update()
                        count += 1
                        keystested.config(text=str(count))
                        pbprogress.set(round((count/10)*100))
                        pb.update()

                else:
                    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    text = pycipher.ColTrans(alphabet[0:int(selected_period.get())]).decipher(get_cipher())
                    text = decrypt.vigenere(text,key.get().upper())
                    cipher_output.delete('1.0',tk.END)
                    cipher_output.insert(tk.INSERT,restore(text))
                    cipher_output.update()
                    pbprogress.set(100)
                    pb.update()

            bestkey.config(text=keys_top[0].cget('text'))

        def crack_vigenere(ctext,pbprogress):
            def key_updater(top10keys):
                top10keys = top10keys[-10:]
                for i in range(10):
                    keys_top[9 - i].config(text=top10keys[i])
            global top10keys
            top10keys = ["" for x in range(10)]
            ctext = process_encryption.process2(ctext)
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            best_overall = -99e9
            count = 0
            for keylength in range(1, 16):
                parentkey = "A" * keylength
                parentscore = fitness.score(decrypt.vigenere(ctext, parentkey))
                parentkey = list(parentkey)
                best_starter_score = parentscore
                best_starter = "".join(parentkey)
                for i in range(keylength):
                    for letter in alphabet:
                        parentkey = list(parentkey)
                        child = parentkey
                        child[i] = letter
                        child = "".join(child)
                        childscore = fitness.score(decrypt.vigenere(ctext, child))
                        if childscore > best_starter_score:
                            best_starter_score = childscore
                            best_starter = child
                        if childscore > best_overall:
                            bestfitness.config(text=str(round(childscore)))
                            top10keys.append(child)
                            key_updater(top10keys)
                            best_overall = childscore
                            best_key = child
                            cipher_output.delete('1.0',tk.END)
                            cipher_output.insert(tk.INSERT,restore(decrypt.vigenere(ctext, best_key)))
                            cipher_output.update()
                        count += 1
                        keystested.config(text=str(count))
                        pbprogress.set(int((count/3120)*100))
                        pb.update()
                    parentkey = best_starter

        def crack_beaufort(ctext,pbprogress):
            global top10keys
            top10keys = ["" for x in range(10)]
            ctext = decrypt.atbash(process_encryption.process2(ctext))
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            best_overall = -99e9
            count = 0
            for keylength in range(1, 16):
                parentkey = "A" * keylength
                parentscore = fitness.score(decrypt.vigenere(ctext, parentkey))
                parentkey = list(parentkey)
                best_starter_score = parentscore
                best_starter = "".join(parentkey)
                for i in range(keylength):
                    for letter in alphabet:
                        parentkey = list(parentkey)
                        child = parentkey
                        child[i] = letter
                        child = "".join(child)
                        childscore = fitness.score(decrypt.vigenere(ctext, child))
                        if childscore > best_starter_score:
                            best_starter_score = childscore
                            best_starter = child
                        if childscore > best_overall:
                            bestfitness.config(text=str(round(childscore)))
                            top10keys.append(decrypt.atbash(child))
                            key_updater(top10keys)
                            best_overall = childscore
                            best_key = child
                            cipher_output.delete('1.0',tk.END)
                            cipher_output.insert(tk.INSERT,restore(decrypt.vigenere(ctext, best_key)))
                            cipher_output.update()
                        count += 1
                        keystested.config(text=str(count))
                        pbprogress.set(int((count/3120)*100))
                        pb.update()
                    parentkey = best_starter

        def crack_caesar(ctext,pbprogress):

            shifted = []
            stringsqr = []
            for i in range(26):
                shifted.append(decrypt.caesar(ctext, 26 - i))
                stringsqr.append(chisqr(shifted[i]))  # Calculate Chi^2 Statistics
                keystested.config(text=str(i+1))
            bestfitness.config(text=str(round(min(stringsqr))))
            key = stringsqr.index(min(stringsqr))  # Key will be shift with lowest Chi^2 Statistic
            decrypted = decrypt.caesar(ctext, 26 - key)
            pbprogress.set(100)
            bestkeys = []
            allkeys = stringsqr[:]
            for i in range(10):
                bestkeys.append(allkeys.index(min(stringsqr)))
                stringsqr.remove(min(stringsqr))
                keys_top[i].config(text=str(bestkeys[i]),font="Courier 11")
            pb.update()
            cipher_output.delete('1.0',tk.END)
            cipher_output.insert(tk.INSERT,restore(decrypted))
            cipher_output.update()

        def crack_coltrans(ctext,pbprogress):

            alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            max_score = -99 * (10 ** 9)
            count = 0
            top10keys = ["" for x in range(10)]
            for i in range(2, 8):
                current_alphabet = alphabet[:i]
                current_alphabet = "".join(current_alphabet)
                perms = [''.join(p) for p in permutations(current_alphabet)]
                for j in range(len(perms)):
                    deciphered = pycipher.ColTrans(perms[j]).decipher(ctext)
                    score = fitness.score(deciphered)
                    if score > max_score:
                        top10keys.append(perms[j])
                        key_updater(top10keys)
                        bestfitness.config(text=str(round(score)))
                        max_score = score
                        cipher_output.delete('1.0', tk.END)
                        cipher_output.insert(tk.INSERT, restore(deciphered))
                        cipher_output.update()
                    count += 1
                    pbprogress.set(round((count/5912)*100))
                    pb.update()
                    keystested.config(text=str(count))

        def crack_polybius(ctext,pbprogress):
            chars = "".join(list(set(ctext)))
            maxkeys = math.factorial(len(chars))
            perms = [''.join(p) for p in permutations(chars)]
            best_score = -99e9
            top10keys = ["" for x in range(10)]
            count = 0
            for key in perms:
                # NOTE: Pycipher has issues if cipher is made up of digits
                deciphered = pycipher.PolybiusSquare("ABCDEFGHIKLMNOPQRSTUVWXYZ", len(chars), key).decipher(ctext)
                score = fitness.score(deciphered)
                if score > best_score:
                    bestfitness.config(text=str(round(score)))
                    top10keys.append(key)
                    key_updater(top10keys)
                    best_score = score
                    best_decryption = deciphered
                    cipher_output.delete('1.0', tk.END)
                    cipher_output.insert(tk.INSERT, restore(best_decryption))
                    cipher_output.update()
                count += 1
                keystested.config(text=str(count))
                pbprogress.set(round((count/maxkeys)*100))
                pb.update()

        def crack_2x2hill(ctext,pbprogress):
            padded = len(ctext)
            if len(ctext) % 2 != 0:
                ctext = ctext + "X"
                padded = 1
            alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            combinations = []
            for i in range(26):
                for j in range(26):
                    combinations.append([i, j])
            cvectors = []
            for i in range(0, len(ctext), 2):
                cvectors.append([alphabet.index(ctext[i+j]) for j in range(2)])
            decryption_score = []
            totalloops = len(combinations)
            count = 0
            for combo in combinations:
                current_decryption = []
                for block in cvectors:
                    current_decryption.append(chr(((block[0] * combo[0] + block[1] * combo[1]) % 26) + 65))
                cipher_output.delete('1.0', tk.END)
                cipher_output.insert(tk.INSERT, restore("".join(current_decryption)))
                cipher_output.update()
                count += 1
                keystested.config(text=str(count))
                pbprogress.set(round((count/totalloops)*100))
                pb.update()
                decryption_score.append(chisqr("".join(current_decryption)))
                bestfitness.config(text=str(round(decryption_score[-1])))
            decryption_score_copy = decryption_score[:]
            best_1 = combinations[decryption_score_copy.index(min(decryption_score))]
            decryption_score.remove(min(decryption_score))
            best_2 = combinations[decryption_score_copy.index(min(decryption_score))]
            for i in range(2):
                best_1[i] = str(best_1[i])
                best_2[i] = str(best_2[i])
            key1 = " ".join(best_1) + " " + " ".join(best_2)
            key2 = " ".join(best_2) + " " + " ".join(best_1)
            decry1 = decrypt.hill2x2(ctext, key1)
            decry2 = decrypt.hill2x2(ctext, key2)
            s1 = fitness.score(decry1)
            s2 = fitness.score(decry2)
            print(padded)
            if s1 > s2:
                cipher_output.delete('1.0', tk.END)
                if padded == 1:
                    complete = restore(decry1[:-1])
                else:
                    complete = restore(decry1)
                cipher_output.insert(tk.INSERT, complete)
                cipher_output.update()
                keys_top[0].config(text=key1)
                keys_top[1].config(text=key2)
            else:
                cipher_output.delete('1.0', tk.END)
                if padded == 1:
                    complete = restore(decry2[:-1])
                else:
                    complete = restore(decry2)
                cipher_output.insert(tk.INSERT, complete)
                cipher_output.update()
                keys_top[0].config(text=key2)
                keys_top[1].config(text=key1)

        def crack_3x3hill(ctext,pbprogress):
            padded = len(ctext)
            if len(ctext) % 3 == 1:
                ctext = ctext + "XX"
                padded = 2
            elif len(ctext) % 3 == 2:
                ctext = ctext + "X"
                padded = 1
            alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            combinations = []
            for i in range(26):
                for j in range(26):
                    for k in range(26):
                        combinations.append([i, j, k])
            print(combinations)
            cvectors = []
            for i in range(0, len(ctext), 3):
                cvectors.append([alphabet.index(ctext[i]), alphabet.index(ctext[i + 1]), alphabet.index(ctext[i+2])])
            print(cvectors)
            decryption_score = []
            totalloops = len(combinations)
            count = 0
            for combo in combinations:
                current_decryption = []
                for block in cvectors:
                    current_decryption.append(chr(((block[0] * combo[0] + block[1] * combo[1] + block[2] * combo[2]) % 26) + 65))
                cipher_output.delete('1.0', tk.END)
                cipher_output.insert(tk.INSERT, restore("".join(current_decryption)))
                cipher_output.update()
                count += 1
                keystested.config(text=str(count))
                pbprogress.set(round((count/totalloops)*100))
                pb.update()
                decryption_score.append(chisqr("".join(current_decryption)))
                bestfitness.config(text=str(round(decryption_score[-1])))
            decryption_score_copy = decryption_score[:]
            best_1 = combinations[decryption_score_copy.index(min(decryption_score))]
            decryption_score.remove(min(decryption_score))
            best_2 = combinations[decryption_score_copy.index(min(decryption_score))]
            decryption_score.remove(min(decryption_score))
            best_3 = combinations[decryption_score_copy.index(min(decryption_score))]
            print(best_1)
            print(best_2)
            print(best_3)
            for i in range(3):
                best_1[i] = str(best_1[i])
                best_2[i] = str(best_2[i])
                best_3[i] = str(best_3[i])
            key1 = " ".join(best_1) + " " + " ".join(best_2) + " " + " ".join(best_3)
            key2 = " ".join(best_1) + " " + " ".join(best_3) + " " + " ".join(best_2)
            key3 = " ".join(best_2) + " " + " ".join(best_1) + " " + " ".join(best_3)
            key4 = " ".join(best_2) + " " + " ".join(best_3) + " " + " ".join(best_1)
            key5 = " ".join(best_3) + " " + " ".join(best_1) + " " + " ".join(best_2)
            key6 = " ".join(best_3) + " " + " ".join(best_2) + " " + " ".join(best_1)

            decry = []
            keylist = []
            for key in (key1,key2,key3,key4,key5,key6):
                keylist.append(key)
                decry.append(decrypt.hill3x3(ctext,key))
            s = []
            for decryption in decry:
                s.append(fitness.score(decryption))
            s2 = s[:]
            for i in range(6):
                x = s2.index(max(s))
                if i == 0:
                    if padded == 1:
                        complete = restore(decry[x][:-1])
                    elif padded == 2:
                        complete = restore(decry[x][:-2])
                    else:
                        complete = restore(decry[x])
                    cipher_output.delete('1.0', tk.END)
                    cipher_output.insert(tk.INSERT, complete)
                    cipher_output.update()
                keys_top[i].config(text=keylist[x],font="Courier 7")
                if i != 5:
                    s.remove(max(s))

        def crack_substitution(ctext,pbprogress):
            stopper.config(state=tk.NORMAL)
            global stop
            stop = False
            pb.config(mode='indeterminate')
            pb.start()
            tested = 0
            maxkey = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            maxscore = -99e9
            parentscore, parentkey = maxscore, maxkey[:]
            # keep going until we are killed by the user
            i = 0
            while True:
                i += 1
                random.shuffle(parentkey)
                deciphered = decrypt.substitution(ctext,parentkey)
                parentscore = fitness.score(deciphered)
                count = 0
                while count < 1000:
                    pb.update()
                    a = random.randint(0, 25)
                    b = random.randint(0, 25)
                    child = parentkey[:]
                    # swap two characters in the child
                    child[a], child[b] = child[b], child[a]
                    deciphered = decrypt.substitution(ctext,child)
                    score = fitness.score(deciphered)
                    # if the child was better, replace the parent with it
                    if score > parentscore:
                        parentscore = score
                        parentkey = child[:]
                        count = 0
                    count = count + 1
                    tested += 1
                    keystested.config(text=str(tested))
                    if stop == True: break
                # keep track of best score seen so far
                if parentscore > maxscore:
                    maxscore, maxkey = parentscore, parentkey[:]
                    bestfitness.config(text=str(round(maxscore)))
                    current_keys = []
                    for i in range(10):
                        current_keys.append(keys_top[i].cget('text'))
                    current_keys = current_keys[:-1]
                    for i in range(1,10):
                        keys_top[i].config(text=current_keys[i-1])
                    keys_top[0].config(text="".join(maxkey)[:15])
                    ss = decrypt.substitution(ctext,maxkey)
                    cipher_output.delete('1.0', tk.END)
                    cipher_output.insert(tk.INSERT, restore(ss))
                    cipher_output.update()
                if stop == True: break
            stopper.config(state=tk.DISABLED)

        def crack_vigenere_affine(ctext,pbprogress):
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            best_overall = -99e9
            coprime_26 = [3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25]  # Removed 1 to save time
            period = selected_period.get()
            if key.get() == "":
                average = []
                for j in range(2, 16):
                    sequence = []
                    for k in range(j):
                        text = list(ctext[k:])
                        n = j
                        output = []
                        i = 0
                        while i < len(text):
                            output.append(text[i])
                            i = i + int(n)
                        phrase = "".join(output)
                        sequence.append(indice_coincidence(phrase))  # Calculate each index of coincidence
                    average.append(sum(sequence) / len(sequence))  # Calculate average IC for each period

                keylength = average.index(max(average)) + 2
            else: keylength = len(key.get())
            count = 0
            top10keys = ["" for x in range(10)]
            actualkey = key.get().upper()
            if period != "-":
                coprime_26 = [int(period)]
            print(coprime_26)
            totaltests = len(coprime_26)*keylength*26
            for a in coprime_26:
                if actualkey == "":
                    parentkey = "A" * keylength
                    print(a)
                    parentscore = fitness.score(decrypt.vigenereaffine(ctext, parentkey, a))
                    parentkey = list(parentkey)
                    best_starter_score = parentscore
                    best_starter = "".join(parentkey)
                    for i in range(keylength):
                        for letter in alphabet:
                            parentkey = list(parentkey)
                            child = parentkey
                            child[i] = letter
                            child = "".join(child)
                            childscore = fitness.score(decrypt.vigenereaffine(ctext, child, a))
                            if childscore > best_starter_score:
                                best_starter_score = childscore
                                best_starter = child
                            if childscore > best_overall:
                                bestfitness.config(text=str(round(childscore)))
                                top10keys.append(child)
                                key_updater(top10keys)
                                best_overall = childscore
                                best_key = child
                                best_a = a
                                cipher_output.delete('1.0', tk.END)
                                cipher_output.insert(tk.INSERT, restore(decrypt.vigenereaffine(ctext, best_key, best_a)))
                                cipher_output.update()
                            count += 1
                            keystested.config(text=str(count))
                            pbprogress.set(round((count/totaltests)*100))
                            pb.update()
                        parentkey = best_starter
                else:
                    bestkey.config(text=str(actualkey))
                    parentscore = fitness.score(decrypt.vigenereaffine(ctext, actualkey, a))
                    if parentscore > best_overall:
                        best_overall = parentscore
                        best_a = a
                        cipher_output.delete('1.0', tk.END)
                        cipher_output.insert(tk.INSERT, restore(decrypt.vigenereaffine(ctext, actualkey, best_a)))
                        cipher_output.update()
                    count += 1
                    keystested.config(text=str(count))
                    pbprogress.set(round((count/len(coprime_26))*100))
                    pb.update()

        def crack_vigenere_scytale(ctext,pbprogress):
            stopper.config(state=tk.NORMAL)
            global stop
            stop = False
            pb.config(mode='indeterminate')
            pb.start()
            top10keys = ["" for x in range(10)]
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            best_overall = -99e9
            best_scytale = -99e9
            count = 0
            for scytale in range(1, 11):
                cipher = pycipher.ColTrans(alphabet[0:scytale + 1]).decipher(ctext)
                for keylength in range(1, 21):
                    parentkey = "A" * keylength
                    parentscore = fitness.score(decrypt.vigenere(cipher, parentkey))
                    parentkey = list(parentkey)
                    best_starter_score = parentscore
                    best_starter = "".join(parentkey)
                    for i in range(keylength):
                        for letter in alphabet:
                            parentkey = list(parentkey)
                            child = parentkey
                            child[i] = letter
                            child = "".join(child)
                            childscore = fitness.score(decrypt.vigenere(cipher, child))
                            if childscore > best_starter_score:
                                best_starter_score = childscore
                                best_starter = child
                            if childscore > best_overall:
                                best_overall = childscore
                                best_key = child
                            pb.update()
                        parentkey = best_starter
                        count += 1
                        keystested.config(text=str(count))
                        if stop == True: break
                    if stop == True: break
                if stop == True: break

                current_scytale = fitness.score(decrypt.vigenere(cipher, best_key))
                if current_scytale > best_scytale:
                    top10keys.append(best_key)
                    key_updater(top10keys)
                    bestfitness.config(text=str(round(current_scytale)))
                    best_scytale = current_scytale
                    scytalenum = scytale
                    cipher_output.delete('1.0', tk.END)
                    cipher_output.insert(tk.INSERT, restore(decrypt.vigenere(cipher,best_key)))
                    cipher_output.update()
            stopper.config(state=tk.DISABLED)



class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page One!!!", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button1 = tk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

        button2 = tk.Button(self, text="Page Two",
                            command=lambda: controller.show_frame(PageTwo))
        button2.pack()


app = Crypt()
app.mainloop()


# from tkinter import *
#
#
# def raise_frame(frame):
#     frame.tkraise()
#
# root = Tk()
# root.geometry('{}x{}'.format(800, 100))
# root.title("Cryptanalysis Toolbox v2.0 by Dulhan Jayalath")
# f1 = Frame(root)
# f2 = Frame(root)
# f3 = Frame(root)
# f4 = Frame(root)
#
# for frame in (f1, f2, f3, f4):
#     frame.grid(row=0, column=0, sticky='news')
# Label(f1,text="Encrypted Text").pack(side="top",anchor=CENTER)
# scrollbar = Scrollbar(f1)
# scrollbar.pack(side="right")
#
# cipher_input = Text(f1, wrap=WORD, yscrollcommand=scrollbar.set,height=5,width=80)
# cipher_input.pack(side="top")
#
# scrollbar.config(command=cipher_input.yview)
#
# Label(f2, text='FRAME 2').pack()
# Button(f2, text='Go to frame 3', command=lambda:raise_frame(f3)).pack()
#
# Label(f3, text='FRAME 3').pack(side='left')
# Button(f3, text='Go to frame 4', command=lambda:raise_frame(f4)).pack(side='left')
#
# Label(f4, text='FRAME 4').pack()
# Button(f4, text='Goto to frame 1', command=lambda:raise_frame(f1)).pack()
#
# raise_frame(f1)
# root.mainloop()         