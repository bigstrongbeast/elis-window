// Элис.exe — запускалка, «как в старых играх на дисках»: сама ничего не делает,
// только стартует python\pythonw.exe app\main.py из своей папки. Весь код открыт рядом, в app\.
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

static class Elis
{
    [STAThread]
    static void Main(string[] args)
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string py = Path.Combine(dir, "python", "pythonw.exe");
        string main = Path.Combine(dir, "app", "main.py");
        if (!File.Exists(py) || !File.Exists(main))
        {
            MessageBox.Show("Не нашла рядом папки python и app.\nПапку «Элис» нужно держать целиком.", "Элис",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        var psi = new ProcessStartInfo(py, "\"" + main + "\" " + string.Join(" ", args))
        {
            WorkingDirectory = Path.Combine(dir, "app"),
            UseShellExecute = false,
        };
        Process.Start(psi);
    }
}
