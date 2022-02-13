# Windows vs. Mac/Linux
ifeq ($(OS), Windows_NT)
	venv_script = .venv\Scripts\activate.bat
	env_activate = $(venv_script)
	python3 = copy /Y .venv\Scripts\python.exe .venv\Scripts\python3.exe && .venv\Scripts\python3.exe --version
	del = del /F /S /Q
else
	venv_script = .venv/bin/activate
	env_activate = . $(venv_script)
	python3 = .venv/bin/python3 --version
	del = rm -rf
endif

all: venv build unit module

$(venv_script): requirements.txt
	python3 -m venv .venv
	${env_activate} \
		&& python3 -m pip install -r requirements.txt

venv: $(venv_script)

deploy: $(venv_script)
	$(env_activate) && cd infrastructure && cdk bootstrap && cdk deploy \
		&& cd ../ &&  python3 main.py

destroy: $(venv_script)
	$(env_activate) && cd infrastructure && yes | cdk destroy

clean:
	$(del) .venv

.PHONY: venv deploy destroy clean