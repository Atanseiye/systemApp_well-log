import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import sys

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from sklearn.preprocessing import MinMaxScaler
except ModuleNotFoundError as e:
    messagebox.showerror("Module Error", f"Missing module: {e.name}\nPlease install it using 'pip install {e.name}'")
    sys.exit(1)

class GeologyApp(tk.Tk):

    def __init__(self, ):
        super().__init__()
        self.title("Geology Data Analysis")
        self.geometry("800x400")


        frame = tk.Frame()
        frame.pack(pady=10)
        
        self.data = None
        self.selected_x_features = []
        self.y_feature = "DEPTH"

        # Top Toolbar
        toolbar = tk.Frame(self, relief=tk.RAISED, bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="📂 Open", command=self.load_data).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Combobox(toolbar, values=["Facies [U]", "Porosity", "Permeability"], width=15).pack(side=tk.LEFT, padx=5)
        ttk.Combobox(toolbar, values=["Tarbert-2 (Zone 2)", "Zone 3", "Zone 4"], width=20).pack(side=tk.LEFT, padx=5)
        self.x_feature_listbox = tk.Listbox(toolbar, selectmode=tk.MULTIPLE,height=1, width=20)
        self.x_feature_listbox.pack(side=tk.LEFT, padx=5)

        self.plot_btn = tk.Button(toolbar, text="Plot Graph", command=self.plot_graph, state=tk.DISABLED)
        self.plot_btn.pack(side=tk.LEFT, padx=10)
        # .pack(side=tk.LEFT, padx=5)
        
        # Tabbed Section
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        tabs = {"Proportion": tk.Frame(notebook), "Thickness": tk.Frame(notebook),
                "Probability": tk.Frame(notebook), "Variograms": tk.Frame(notebook)}
        
        for name, frame in tabs.items():
            notebook.add(frame, text=name)
        
        # Canva for plot display
        self.canvas_frame = tk.Frame()
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
    # Component to load the data
    def load_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return
        
        try:
            self.data = pd.read_excel(file_path)
            if self.data is not None:
                self.data.replace(-999.25, pd.NA, inplace=True)
                self.data.dropna(inplace=True)

                for column in self.data.columns:
                    if self.data[column].dtype in ['float64', 'int64'] and column != self.y_feature:
                        lower_bound = self.data[column].quantile(0.05)
                        upper_bound = self.data[column].quantile(0.98)
                        self.data = self.data[(self.data[column] >= lower_bound) & (self.data[column] <= upper_bound)]
                
            #     self.display_data() ----> To display the data
            # self.display_data() ----> To display the data
            if self.y_feature not in self.data.columns:
                messagebox.showerror("Error", f"'{self.y_feature}' column not found in dataset.")
                return
            
            x_features = [col for col in self.data.columns if col != self.y_feature]
            self.x_feature_listbox.delete(0, tk.END)
            for feature in x_features:
                self.x_feature_listbox.insert(tk.END, feature)
            
            self.plot_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    # Display the data
    def display_data(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.data.columns)
        self.tree["show"] = "headings"
        
        for col in self.data.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        for _, row in self.data.iterrows():
            self.tree.insert("", tk.END, values=row.tolist())

    # Scaling Feature
    def scale_features(self, features):
        scaler = MinMaxScaler()
        scaled_values = scaler.fit_transform(self.data[features])
        return pd.DataFrame(scaled_values, columns=features)
    

    def plot_graph(self):
        if self.data is None:
            messagebox.showerror("Error", "No data loaded.")
            return
        
        selected_indices = self.x_feature_listbox.curselection()
        self.selected_x_features = [self.x_feature_listbox.get(i) for i in selected_indices]
        
        if not self.selected_x_features:
            messagebox.showerror("Error", "Please select at least one feature for the X-axis.")
            return
        
        selected_x_features_limited = self.selected_x_features[:7]  # Limit to 7 features
        
        if not all(self.data[feature].min() >= 0 and self.data[feature].max() <= 1 for feature in selected_x_features_limited):
            scaled_data = self.scale_features(selected_x_features_limited)
        else:
            scaled_data = self.data[selected_x_features_limited]
        
        depth_range = self.data[self.y_feature].max() - self.data[self.y_feature].min()
        fig_height = max(5, depth_range / 10)  # Adjust height dynamically
        fig, ax = plt.subplots(figsize=(8, fig_height))
        
        for feature, original_feature in zip(scaled_data.columns, selected_x_features_limited):
            ax.plot(scaled_data[feature], self.data[self.y_feature], label=original_feature)
            # self.apply_shading(ax, original_feature)
        
        ax.set_xlabel("Selected Features (Scaled)")
        ax.set_ylabel(self.y_feature)
        ax.set_title("Plot of Selected Features vs Depth")
        ax.legend()
        ax.set_ylim(self.data[self.y_feature].max(), self.data[self.y_feature].min())  # Ensure y-axis starts from 0 to last value
        
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = GeologyApp()
    app.mainloop()