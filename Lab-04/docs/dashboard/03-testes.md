## Como cada teste funciona
- **Pearson (r)** mede quanto LOC e defeitos variam juntos em linha reta, usando os próprios valores; poucas classes muito grandes podem puxar o coeficiente.
- **Spearman (ρ)** troca os valores pelos postos (1ª, 2ª, … maior classe) e mede se, em geral, classes maiores têm mais defeitos, mesmo sem relação linear; empates, como os muitos zeros, recebem o posto médio.
- Os dois convertem a correlação na estatística **t com n − 2 graus de liberdade** e usam o mesmo α = 5% bicaudal.

## O que observar
A curva preta é a distribuição de t quando H₀ é verdadeira; a área hachurada são os 5% mais extremos (|t| > 2,05, metade em cada cauda); a área colorida além de ±t observado é o **p-valor**.

## Conclusão
No conjunto simulado com ρ = 0,5, Pearson obteve t = 3,48 (p = 0,002) e Spearman t = 2,58 (p = 0,015): os dois caem na região de rejeição e acertam, pois a associação existe. O p-valor é a chance de um t tão extremo **se H₀ fosse verdadeira**, não a chance de H₀ ser verdadeira. Com a nula por permutação ativada, ela coincide com a curva t no Spearman, mas é irregular no Pearson, dominada por poucas classes enormes: um primeiro sinal de que o p-valor do Pearson pode ser pouco confiável com estes dados. Um único conjunto, porém, não diz qual teste é melhor; é isso que as seções 4 e 5 medem.
