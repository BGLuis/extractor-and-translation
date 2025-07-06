<div align="center">

  ![Python][Python.io]


  [![Contributors][contributors-shield]][contributors-url]
  [![Forks][forks-shield]][forks-url]
  [![Stargazers][stars-shield]][stars-url]
  [![Issues][issues-shield]][issues-url]
  [![Unlicense License][license-shield]][license-url]

  <!-- <a href="https://github.com/bgluis/extractor-and-translation/">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a> -->

  <h3>Extractor and Translation</h3>
  Tradutor de jogos
</div>

# 📖 Sobre
Descreva o que é o seu projeto e pra que ele serve

# 📋 Motivo
O por que esse projeto existe?

# 💻 Como iniciar
Instruções de como executar o seu projeto

## Pré-requisitos
Certifique-se de ter o Python 3.10 instalado. Você pode baixá-lo [aqui](https://www.python.org/downloads/).

## Instalação

### Usando Docker (recomendado)
1. Certifique-se de ter o [Docker](https://docs.docker.com/get-docker/) e o [docker-compose](https://docs.docker.com/compose/install/) instalados.
2. No Linux, permita acesso ao X11 para aplicações gráficas:
   ```sh
   xhost +local:docker
   ```
3. Clone o repositório:
   ```sh
   git clone https://github.com/bgluis/extractor-and-translation.git
   cd extractor-and-translation
   ```
4. Construa e suba o container:
   ```sh
   docker-compose up --build
   ```
5. Para abrir um terminal interativo dentro do container:
   ```sh
	docker-compose run --service-ports app /bin/bash
	python main.py
   ```

### Instalação manual (sem Docker)
1. Certifique-se de ter o Python 3.11 instalado. Você pode baixá-lo [aqui](https://www.python.org/downloads/).
2. Crie um ambiente virtual:
   ```sh
   python3.11 -m venv venv
   ```
3. Ative o ambiente virtual:
   - No Windows:
     ```sh
     venv\Scripts\activate
     ```
   - No macOS/Linux:
     ```sh
     source venv/bin/activate
     ```
4. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```

## Uso
1. Execute o script principal:
   ```sh
   python main.py
   ```
2. Siga as instruções exibidas no terminal ou na interface gráfica.

Pronto! Agora você deve estar apto a usar o projeto.

# 🤝 Contribuidores
 <a href = "https://github.com/bgluis/extractor-and-translation/graphs/contributors">
   <img src = "https://contrib.rocks/image?repo=bgluis/extractor-and-translation"/>
 </a>

 <!-- Links -->
 <!-- https://github.com/iuricode/readme-template-->
[repossitory-path]: bgluis/extractor-and-translation/
[contributors-shield]: https://img.shields.io/github/contributors/bgluis/extractor-and-translation.svg?style=for-the-badge
[contributors-url]: https://github.com/bgluis/extractor-and-translation/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/bgluis/extractor-and-translation.svg?style=for-the-badge
[forks-url]: https://github.com/bgluis/extractor-and-translation/network/members
[stars-shield]: https://img.shields.io/github/stars/bgluis/extractor-and-translation.svg?style=for-the-badge
[stars-url]: https://github.com/bgluis/extractor-and-translation/stargazers
[issues-shield]: https://img.shields.io/github/issues/bgluis/extractor-and-translation.svg?style=for-the-badge
[issues-url]: https://github.com/bgluis/extractor-and-translation/issues
[license-shield]: https://img.shields.io/github/license/bgluis/extractor-and-translation.svg?style=for-the-badge
[license-url]: https://github.com/bgluis/extractor-and-translation/blob/master/LICENSE.txt

[Python.io]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
