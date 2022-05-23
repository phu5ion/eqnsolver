# Equation Solver
Guy writes equation on website. Machine model parses equation and predicts solution.

# Setup
- Do git clone stuff as usual
- Highly suggested to create a virtual environment for project, do so by:
> python3 -m venv eqnenv
- Install dependencies via requirements.txt
> pip3 install -r requirements.txt
- Install LocalTunnel (To expose your localhost to interweb)
> brew install localtunnel

# Run
- Go to project directory on your console (Terminal for mac)
> cd {Drag and Drop eqnsolver folder onto Terminal}
- Run project virtual environment if you chose to set one up
> source eqnenv/bin/activate
- Start flask app as usual, you can view the app locally via http://127.0.0.1:5000
> python3 -m flask run

- Now, create a new console window and startup local tunnel connection. ***NOTE: It has to be eqnsolver, don't change the subdomain.***
> lt -p 5000 -s eqnsolver
- You can now view the webpage via the url link: https:eqnsolver.loca.lt/
