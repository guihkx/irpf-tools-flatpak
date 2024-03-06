## About

This script generates Flatpak [sources](https://docs.flatpak.org/en/latest/manifests.html#modules) for [IRPF](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda)🇧🇷 apps [on Flathub](https://github.com/search?q=org%3Aflathub+br.gov.fazenda.receita&type=repositories).

These sources are composed of ZIP files, and upon extracting them, we get a single XML file, which should be installed to the `lib/resources` directory, where other XML files already exist.

These XML files are used by IRPF to keep its information database up to date, and they are updated independently from the main app:

At start up, IRPF checks if they are up to date, and if they are not, it will download these ZIP files and try to extract the XML files in them to the same location where `irpf.jar` is.

However, on the Flatpak package, that location is write-protected, and so IRPF is not able to perform the extraction successfully, leaving the program outdated.

So, the purpose of this tool is to include these updated XML files at the packaging stage.

## Usage

```sh
# 1. Clone the repository
git clone https://github.com/guihkx/irpf-tools-flatpak.git
# 2. Navigate to this folder
cd irpf-tools-flatpak/sources-generator/
# 3. Create a Python environment
python -m venv env
# 4. Activate the environment
source env/bin/activate
# 5. Install required dependencies
pip install -r requirements.txt
# 6. Run the script
./generate.py --help
```
