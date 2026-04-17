from pypix.pix import Pix


def generate_pix_payload(amount, travel_id, driver_id):
    """
    Gera o payload PIX Copia e Cola usando a biblioteca pypix.
    TXID é gerado para identificar a viagem e o motorista.
    """
    pix = Pix()

    # Dados da Plataforma (Central)
    pix.set_key("cleiton.leonel@gmail.com")
    pix.set_name_receiver("DriveMatch Bot")
    pix.set_city_receiver("SAO PAULO")

    # Dados da Transação
    pix.set_amount(float(amount))

    # TXID: Identificador da transação no extrato (set_identification no pypix)
    # Máximo 25 caracteres no PIX estático
    txid = f"DM{travel_id}D{driver_id}"
    pix.set_identification(txid)

    try:
        # No pypix, o método get_br_code() gera o payload final
        return pix.get_br_code()
    except Exception as e:
        print(f"Erro na geração do PIX: {e}")
        return None


def verify_payment_status(travel_id):
    """
    Simula a consulta à API do Mercado Pago para verificar se o PIX foi pago.
    No futuro, esta função consultará o gateway real usando o TXID.
    """
    # TODO: Implementar consulta real ao Mercado Pago
    import logging
    logging.info(f"MOCK: Verificando status do pagamento para a viagem {travel_id}...")
    return True
