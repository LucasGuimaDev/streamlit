import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide', menu_items={"Get help":"https://www.youtube.com/", "About":"Este relatório tem como base apenas estudos."}) # setando para que o dashboard pegue a tela toda e não fique centralizado

## Funções
def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /=1000
    return f'{prefixo} {valor:.2f} milhões'

# ---------------- LOGIN ---------------- #

def login():

    st.title("🔐 Login")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        users = st.secrets["users"]

        if username in users:

            if password == users[username]:
                st.session_state["logged"] = True
                st.session_state["user"] = username
                st.rerun()

            else:
                st.error("Senha incorreta")

        else:
            st.error("Usuário não encontrado")


if "logged" not in st.session_state:
    st.session_state["logged"] = False


if not st.session_state["logged"]:
    login()
    st.stop()

# ---------------- APP ---------------- #

st.sidebar.success(f"Logado como: {st.session_state['user']}")

if st.sidebar.button("Logout"):
    st.session_state["logged"] = False
    st.rerun()

st.title('DASHBOARD DE VENDAS')

url = 'https://labdados.com/produtos'

# criando o filtro dos dados direto na chamada API

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes) # aqui eu criei um fitlro com as regiões que passei na lista

if regiao == 'Brasil': # se selecionarmos a opção de Brasil então região fica em branco e não filtra nada
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True) # aqui criei um filtro para os anos dos dados

if todos_anos: # dados, é um checkbox que se selecionado não faz nada
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023) # mas caso o checkbox não seja selecionado ai cria um slider que seleciona o ano



# os dados seleicionados a partir dos filtros acima são passados diretamente na chamada da API, não sendo necessário filtrar os dados depois de coletados
query_string = {'regiao':regiao.lower(), 'ano':ano}


# deixei abaixo uma amostra dos dados em csv para caso o link de ruim
#dados = pd.read_csv(r"C:\Users\lucas\Desktop\alura\Alura-streamlit\dados.csv", sep=",")


response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format= '%d/%m/%Y')


filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique()) # aqui criei um filtro de multiseleção dos vendedores
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)] # os vendedores selecionados filtram os dados

## Tabelas

### Tabelas de receita
receitas_estados = dados.groupby('Local da compra')[['Preço']].sum()
receitas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receitas_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_por_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()

### Tabelas de quantidade de vendas

quantidade_estados = dados.groupby('Local da compra').size().reset_index(name='Quantidade por estado').sort_values('Quantidade por estado', ascending=False)
quantidade_estados['Local da compra'] = quantidade_estados['Local da compra'].astype(str)
dados['Local da compra'] = dados['Local da compra'].astype(str) 
dados_filtrados =  dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]
quantidade_estados = quantidade_estados.merge(dados_filtrados, on='Local da compra')

quantidade_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M')).size().reset_index(name='Quantidade por mes')    
quantidade_mensal['Ano'] = quantidade_mensal['Data da Compra'].dt.year
quantidade_mensal['Mês'] = quantidade_mensal['Data da Compra'].dt.month_name()


quantidade_por_categoria = dados.groupby('Categoria do Produto').size().sort_values(ascending=False)
print(quantidade_por_categoria)
print(receita_por_categoria)
### Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos

### Receitas
fig_mapa_receita = px.scatter_geo(receitas_estados, # Aqui passo a base de dados
                                  lat='lat', # Aqui nesse parâmetro passo onde ta a informação de latitude
                                  lon='lon', # Parâmetro onde passo a informação de longitude
                                  scope='south america', # Por default ele traz o mapa do mundo todo, aqui peguei somente da américa do sul
                                  size='Preço', # Aqui identifico o tamanho dos marcadores do gráfico a partir da coluna preço
                                  template='seaborn', # Aqui passo o template do seaborn, formato visual
                                  hover_name= 'Local da compra', # Aqui passo a informação que eu quero que mostre quando passa o mouse por cima
                                  hover_data= {'lat':False, 'lon':False}, # Aqui eu removo a informação de lat o lon do tooltip que aparece com as informações quando passo o mouse
                                  title= 'Receita por estado' # titulo do mapa
                                  )

fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mês', # eixo x vai ser o mês
                             y = 'Preço', # Eixo y vai ser o preço
                             markers=True, # habilitei os marcadores
                             range_y=(0, receita_mensal.max()), # aqui eu coloquei que o gráfico vai iniciar em 0 e terminar no valor máximo de receita mensal 
                             color= 'Ano', # Alterando a cor da linha a partir do ano
                             line_dash='Ano', # Alterando o formato da linha a partir do ano
                             title = 'Receita mensal'
                            )
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receitas_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto=True, # indica no gráfico o valor em cada coluna,
                             title= 'Top estados (receita)')

fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_por_categoria,
                                color_discrete_sequence=["#e9214c"],
                                text_auto=True, # indica no gráfico o valor em cada coluna,
                                title= 'Receitas por categoria'
                                )

fig_receita_categorias.update_layout(yaxis_title = 'Receita')

### Quantidade

fig_mapa_quantidade = px.scatter_geo(quantidade_estados, # Aqui passo a base de dados
                                  lat='lat', # Aqui nesse parâmetro passo onde ta a informação de latitude
                                  lon='lon', # Parâmetro onde passo a informação de longitude
                                  scope='south america', # Por default ele traz o mapa do mundo todo, aqui peguei somente da américa do sul
                                  size='Quantidade por estado', # Aqui identifico o tamanho dos marcadores do gráfico a partir da coluna quantidade
                                  template='seaborn', # Aqui passo o template do seaborn, formato visual
                                  hover_name= 'Local da compra', # Aqui passo a informação que eu quero que mostre quando passa o mouse por cima
                                  hover_data= {'lat':False, 'lon':False}, # Aqui eu removo a informação de lat o lon do tooltip que aparece com as informações quando passo o mouse
                                  title= 'Quantidade por estado' # titulo do mapa
                                  )

fig_quantidade_mensal = px.line(quantidade_mensal,
                             x = 'Mês', # eixo x vai ser o mês
                             y = 'Quantidade por mes', # Eixo y vai ser a quantidade
                             markers=True, # habilitei os marcadores
                             range_y=(0, quantidade_mensal.max()), # aqui eu coloquei que o gráfico vai iniciar em 0 e terminar no valor máximo de quantidade mensal 
                             color= 'Ano', # Alterando a cor da linha a partir do ano
                             line_dash='Ano', # Alterando o formato da linha a partir do ano
                             title = 'Quantidade mensal'
                            )
fig_quantidade_mensal.update_layout(yaxis_title = 'Quantidade')

fig_quantidade_estados = px.bar(quantidade_estados.head(),
                             x = 'Local da compra',
                             y = 'Quantidade por estado',
                             text_auto=True, # indica no gráfico o valor em cada coluna,
                             title= 'Top estados (quantidade)')

fig_quantidade_categorias = px.bar(quantidade_por_categoria,
                                color_discrete_sequence=["#e9214c"],
                                text_auto=True, # indica no gráfico o valor em cada coluna,
                                title= 'Quantidade por categoria'
                                )

fig_quantidade_categorias.update_layout(yaxis_title = 'Quantidade')

## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores']) # aqui eu estou criando abas para mostrar os dados


with aba1:
    coluna1, coluna2 = st.columns(2) # aqui eu crio duas colunas e logo abaixo coloco os dados de cada coluna
    with coluna1:
        st.metric('receita de vendas', formata_numero(dados['Preço'].sum(), 'R$'), help="Essa métrica mostra o total da receita de vendas")
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]), help="Essa métrica mostra a quantidade de vendas")
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)




with aba2:
    coluna1, coluna2 = st.columns(2) # aqui eu crio duas colunas e logo abaixo coloco os dados de cada coluna
    with coluna1:
        st.metric('receita de vendas', formata_numero(dados['Preço'].sum(), 'R$'), help="Essa métrica mostra o total da receita de vendas")
        st.plotly_chart(fig_mapa_quantidade, use_container_width=True)
        st.plotly_chart(fig_quantidade_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]), help="Essa métrica mostra a quantidade de vendas")
        st.plotly_chart(fig_quantidade_mensal, use_container_width=True)
        st.plotly_chart(fig_quantidade_categorias, use_container_width=True)
   



with aba3:
    qtd_total_vendedores = dados['Vendedor'].drop_duplicates().count()
    qtd_vendedores = st.number_input("Quantidade de vendedores", 2, qtd_total_vendedores, 5)
    coluna1, coluna2 = st.columns(2) # aqui eu crio duas colunas e logo abaixo coloco os dados de cada coluna
    with coluna1:
        st.metric('receita de vendas', formata_numero(dados['Preço'].head(qtd_vendedores).sum(), 'R$'), help="Essa métrica mostra o total da receita de vendas")
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x= 'sum',
                                        y= vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receitas)')
        fig_receita_vendedores.update_layout(yaxis_title = 'Vendedores')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.head(qtd_vendedores).shape[0]), help="Essa métrica mostra a quantidade de vendas")
        vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x= 'count',
                                        y= vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade)')
        vendas_vendedores.update_layout(yaxis_title = 'Vendedores')
        st.plotly_chart(vendas_vendedores)

