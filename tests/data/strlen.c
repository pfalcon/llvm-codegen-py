unsigned int _strlen(char *p)
{
    unsigned int l = 0;
    while (*p++) l++;
    return l;
}
