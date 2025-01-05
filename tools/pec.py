
"""
uint16_t CalcPEC10(bool bIsRxCmd, uint8_t nLength, uint8_t *pDataBuf)
{
    const uint16_t pecD10 = 0x0200, XOR = 0x08F;
    int maxBit = ((nLength - 2) * 8) + 6;
    int bitCounter = 0;
    uint16_t pec = 0x0010;
    int nBytes = nLength;
    while (true)
    {
        nBytes--;
        if (nBytes < 0) return pec;
        uint8_t iter8 = pDataBuf[nLength];
        for (uint8_t mask = 0x80; mask > 0x00; mask >>= 1, bitCounter++)
        {
            if (bitCounter == maxBit) return pec;
            bool wantXOR = ((mask & iter8) != 0) ^ ((pec & pecD10) != 0);
            pec <<= 1;
            if (wantXOR) pec ^= XOR;
            pec &= 0x3FF;
        }
    }
}
"""

def pec10_calc(bIsRxCmd, nLength, data):
    nRemainder = 16
    nPolynomial = 8
    for nByteIndex in range(nLength):
        nRemainder ^= (data[nByteIndex] << 2) & 0xffff
        for nBitIndex in range(8, 0, -1):
            if ((nRemainder & 0x200) > 0):
                nRemainder = (nRemainder << 1) & 0xffff
                nRemainder = (nRemainder ^ nPolynomial) & 0xffff
            else:
                nRemainder = (nRemainder << 1) & 0xffff
    print(hex(nRemainder))
    #nRemainder ^= ((data[nLength] & 0xFC) << 2) & 0xffff
    print(hex(nRemainder))

    for nBitIndex in range(6, 0, -1):
        if ((nRemainder & 0x200) > 0):
            nRemainder = (nRemainder << 1) & 0xffff
            nRemainder = (nRemainder ^ nPolynomial) & 0xffff
        else:
            nRemainder = (nRemainder << 1) & 0xffff
    print(hex(nRemainder))
    out = (nRemainder & 0x3FF)
    print(hex(out))

pec10_calc(True, 6, [0xd9, 0x5b, 0x00, 0x08, 0x5d, 0xe3, 0x35, 0xd3])

"""
uint16_t pec10_calc( bool bIsRxCmd, int nLength, uint8_t *pDataBuf)
{
    uint16_t nRemainder = 16u; /* PEC_SEED */
    /* x10 + x7 + x3 + x2 + x + 1 <- the CRC10 polynomial 100 1000 1111 */
    uint16_t nPolynomial = 0x8Fu;
    uint8_t nByteIndex, nBitIndex;

    for (nByteIndex = 0u; nByteIndex < nLength; ++nByteIndex)
    {
        /* Bring the next byte into the remainder. */
        nRemainder ^= (uint16_t)((uint16_t)pDataBuf[nByteIndex] << 2u);

        /* Perform modulo-2 division, a bit at a time.*/
        for (nBitIndex = 8u; nBitIndex > 0u; --nBitIndex)
        {
            /* Try to divide the current data bit. */
            if ((nRemainder & 0x200u) > 0u)
            { /* equivalent to remainder & 2^14 simply check for MSB */
                nRemainder = (uint16_t)((nRemainder << 1u));
                nRemainder = (uint16_t)(nRemainder ^ nPolynomial);
            }
            else
            {
                nRemainder = (uint16_t)(nRemainder << 1u);
            }
        }
    }

    /* If array is from received buffer add command counter to crc calculation */
    if (bIsRxCmd == true)
    {
        nRemainder ^= (uint16_t)(((uint16_t)pDataBuf[nLength] & (uint8_t)0xFC) << 2u);
    }
    /* Perform modulo-2 division, a bit at a time */
    for (nBitIndex = 6u; nBitIndex > 0u; --nBitIndex)
    {
        /* Try to divide the current data bit */
        if ((nRemainder & 0x200u) > 0u)
        {
            nRemainder = (uint16_t)((nRemainder << 1u));
            nRemainder = (uint16_t)(nRemainder ^ nPolynomial);
        }
        else
        {
            nRemainder = (uint16_t)((nRemainder << 1u));
        }
    }
    return ((uint16_t)(nRemainder & 0x3FFu));
}
"""

