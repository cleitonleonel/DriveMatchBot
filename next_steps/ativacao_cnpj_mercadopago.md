# 🏢 Guia de Ativação: Mercado Pago CNPJ para Payouts

Siga este passo a passo para transformar sua integração em uma operação profissional com saques automáticos via conta jurídica.

---

## 1. Migração da Conta (CPF para CNPJ)
O Mercado Pago permite que você migre sua conta ou crie uma nova. Para automação de Payouts, o ideal é uma conta **Business**.

1.  **Acesse as Configurações**: Vá em `Seu Perfil` > `Dados da sua conta`.
2.  **Alterar Tipo de Conta**: Procure a opção "Alterar para conta de vendedor" ou "Migrar para CNPJ".
3.  **Envio de Documentos**: Você precisará enviar o cartão CNPJ e, possivelmente, o contrato social da empresa.
4.  **Validação**: O Mercado Pago leva de 24h a 48h para validar os dados.

---

## 2. Criação da Aplicação (Portal Developer)
Com a conta CNPJ ativa, você deve criar as chaves de acesso.

1.  Acesse o [Painel do Desenvolvedor](https://www.mercadopago.com.br/developers/panel/app).
2.  Clique em **"Criar Nova Aplicação"**.
3.  **Nome do Projeto**: Sugestão: `DriveMatchBot_API`.
4.  **Tipo de solução**: Selecione "Pagamentos online".
5.  **Produto**: Escolha "Checkout Transparente" ou "API de Pagamentos".

---

## 3. Ativação das Credenciais de Produção
Para que o bot possa movimentar dinheiro real, você precisa solicitar a ativação.

1.  No menu lateral da sua aplicação, clique em **"Credenciais de Produção"**.
2.  **Formulário de Ativação**: Você precisará preencher um formulário chamado "Homologação".
    *   **Indústria**: Serviços de Transporte / Tecnologia.
    *   **Site/URL**: Se não tiver um site, use o link do seu próprio Bot do Telegram ou sua página de termos de uso.
3.  **Termos de Uso**: Aceite e salve. Suas chaves `ACCESS_TOKEN` de produção serão liberadas.

---

## 4. Habilitando a API de Payouts (Disbursements)
Esta é a parte crucial para os saques automáticos. Por padrão, o Mercado Pago libera "Recebimento". O "Envio" (Payout) pode exigir um passo extra:

1.  **Suporte ao Desenvolvedor**: Com as credenciais de produção em mãos, envie uma mensagem ao suporte via [Portal de Ajuda do Desenvolvedor](https://www.mercadopago.com.br/developers/pt/support).
2.  **Solicitação**: Peça a liberação do escopo de `payouts` ou `transfers` para sua aplicação. 
    *   *Exemplo: "Gostaria de habilitar a API de Payouts para realizar repasses automáticos de motoristas em minha plataforma de mobilidade."*
3.  **Dashboard**: Verifique se no seu painel de aplicação apareceu a opção de "Saques" ou "Transferências".

---

## 5. Implementação no Bot
Assim que as chaves de produção estiverem ativas e o escopo de Payout liberado:

1.  Pegue o seu **Access Token de Produção**.
2.  Substitua no arquivo de configuração do Bot.
3.  Ative o módulo de controle automático (baseado no rascunho em `next_steps/mercadopago_payouts.py`).

> [!IMPORTANT]
> **Segurança**: Nunca compartilhe seu Access Token de Produção com ninguém. Ele dá controle total sobre o saldo da sua conta bancária do Mercado Pago.

> [!TIP]
> Enquanto a conta CNPJ não é aprovada, você pode continuar usando o modelo **Semi-Automático** que deixamos pronto, ele funciona perfeitamente para validar seu negócio enquanto a burocracia do banco é processada.
