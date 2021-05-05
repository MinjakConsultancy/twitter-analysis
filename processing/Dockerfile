FROM continuumio/miniconda3
RUN conda create -n env python=3.8
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

WORKDIR /twitter

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt 

COPY ./. .

CMD python $PYTHON_COMMAND