
#if 1

// https://www.eevblog.com/forum/programming/crc32-half-bytenibble-lookup-table-algorithm/

static const uint32_t crc32_posix_lut[16] = {
	0x00000000, 0x04C11DB7, 0x09823B6E, 0x0D4326D9,
	0x130476DC, 0x17C56B6B, 0x1A864DB2, 0x1E475005,
	0x2608EDB8, 0x22C9F00F, 0x2F8AD6D6, 0x2B4BCB61,
	0x350C9B64, 0x31CD86D3, 0x3C8EA00A, 0x384FBDBD
};

uint32_t crc32_fast(uint32_t crc, uint8_t data) {
	crc ^= (uint32_t)data << 24;
	crc = (crc << 4) ^ crc32_posix_lut[crc >> 28];
	crc = (crc << 4) ^ crc32_posix_lut[crc >> 28];
	return crc;
}

#else

uint32_t crc32_fast(uint32_t crc, uint32_t data)
{
    crc = crc ^ data;
    for (int i = 0; i < 32; i++)
        if (crc & 0x80000000) crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF;
        else crc = (crc << 1) & 0xFFFFFFFF;
    return crc;
}

#endif
