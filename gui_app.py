
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
from pathlib import Path

PROJECT = Path.home() / "network-sim" / "ns3-mmwave"
OUTPUT = PROJECT / "received_message.txt"


class MessageDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("UI 1 - Sender")
        self.root.geometry("430x280")
        self.root.resizable(False, False)

        self.busy = False
        self.last_output = None
        self.output_position = 0

        # Sender window
        tk.Label(
            root,
            text="UI 1 - MESSAGE SENDER",
            font=("Arial", 15, "bold")
        ).pack(pady=15)

        tk.Label(
            root,
            text="Enter your message:"
        ).pack()

        self.entry = tk.Entry(root, width=42, font=("Arial", 12))
        self.entry.pack(pady=10)
        self.entry.insert(0, "Hello, how are you?")

        self.status = tk.Label(root, text="Ready to send")
        self.status.pack(pady=5)

        self.send_button = tk.Button(
            root,
            text="Send through NS-3",
            command=self.send_message,
            width=22
        )
        self.send_button.pack(pady=10)

        # Receiver window
        self.receiver = tk.Toplevel(root)
        self.receiver.title("UI 2 - Receiver")
        self.receiver.geometry("480x330")
        self.receiver.resizable(False, False)

        tk.Label(
            self.receiver,
            text="UI 2 - RECEIVER",
            font=("Arial", 15, "bold")
        ).pack(pady=12)

        self.messages = tk.Text(
            self.receiver,
            width=53,
            height=13,
            font=("Arial", 11),
            wrap="word",
            state="disabled"
        )
        self.messages.pack(padx=10, pady=8)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.receiver.protocol("WM_DELETE_WINDOW", self.close)

        self.root.after(300, self.poll_output)

    def send_message(self):
        message = self.entry.get()

        # Keep spaces and punctuation; reject only empty messages.
        if not message.strip():
            messagebox.showwarning(
                "Empty message",
                "Please enter a message before sending."
            )
            return

        if self.busy:
            return

        self.last_output = None
        self.busy = True
        self.send_button.config(state="disabled")
        self.status.config(text="Sending through NS-3...")

        threading.Thread(
            target=self.run_simulation,
            args=(message,),
            daemon=True
        ).start()


    def run_simulation(self, message):
        try:
            message_file = PROJECT / "message_to_send.txt"

            # Save the complete message, preserving spaces and punctuation.
            message_file.write_text(message, encoding="utf-8")

            # Clear any previous receiver output.
            OUTPUT.write_text("", encoding="utf-8")

            result = subprocess.run(
	    [
	        "./ns3",
	        "run",
	        "scratch/gui-network",
	        "--",
	        f"--output={OUTPUT}"
	    ],)
		
            if result.returncode != 0:
                error = result.stderr or result.stdout or "NS-3 simulation failed."
                self.root.after(
                    0, lambda e=error: self.show_error(e)
                )
                return

            # Verify that Node 2 actually received the complete message.
            received = (
                OUTPUT.read_text(encoding="utf-8")
                if OUTPUT.exists()
                else ""
            )

            if received != message:
                error = (
                    "The simulation completed, but the received message "
                    "does not match the sent message.\n\n"
                    f"Expected: {message!r}\n"
                    f"Received: {received!r}\n\n"
                    f"Simulation output:\n{result.stdout}"
                )
                self.root.after(
                    0, lambda e=error: self.show_error(e)
                )
                return

            self.root.after(
                0,
                lambda m=message: self.status.config(
                    text=f"Delivered successfully: {m[:30]}"
                )
            )

        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                lambda: self.show_error("NS-3 simulation timed out.")
            )

        except Exception as exc:
            error = str(exc)
            self.root.after(
                0, lambda e=error: self.show_error(e)
            )

        finally:
            self.root.after(0, self.finish_send)

    def poll_output(self):
        try:
            if OUTPUT.exists():
                content = OUTPUT.read_text(encoding="utf-8")

                # Show newly received output, including repeated messages.
                if content != self.last_output and content:
                    self.last_output = content

                    self.messages.config(state="normal")
                    self.messages.insert(
                        "end",
                        f"Node 2 received: {content}\n"
                    )
                    self.messages.see("end")
                    self.messages.config(state="disabled")

        except OSError:
            pass

        if self.root.winfo_exists():
            self.root.after(300, self.poll_output)

    def show_error(self, error):
        self.status.config(text="Transmission failed")
        messagebox.showerror("NS-3 Error", error[-3000:])

    def finish_send(self):
        self.busy = False

        try:
            if self.root.winfo_exists():
                self.send_button.config(state="normal")
        except tk.TclError:
            pass

    def close(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MessageDemo(root)
    root.mainloop()
